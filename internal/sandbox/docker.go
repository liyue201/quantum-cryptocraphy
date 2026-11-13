package sandbox

import (
	"bytes"
	"context"
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"time"
)

// dockerRunner compiles and runs user code in an isolated container via Docker (production hardening path).
type dockerRunner struct{}

// Run mounts the code into a disposable container: --network none, memory/CPU limits, dropped capabilities.
func (d *dockerRunner) Run(code, lang string, timeout time.Duration) (*Result, error) {
	if len(code) > maxCodeLen {
		return nil, errors.New("code too long")
	}
	if timeout <= 0 || timeout > maxTimeout {
		timeout = maxTimeout
	}

	dir, err := os.MkdirTemp("", "qcc-docker-sandbox-*")
	if err != nil {
		return nil, err
	}
	defer os.RemoveAll(dir)

	// Python backend runs with python3 directly; go backend builds via `go run`.
	fileName, image, cmd := "main.go", "golang:1.25-alpine", []string{"go", "run", "/app/main.go"}
	if lang == "python" {
		fileName, image = "main.py", "python:3.12-slim"
		cmd = []string{"python3", "/app/main.py"}
	}
	if err := os.WriteFile(filepath.Join(dir, fileName), []byte(code), 0o600); err != nil {
		return nil, err
	}

	ctx, cancel := context.WithTimeout(context.Background(), buildLimit)
	defer cancel()

	dockerArgs := []string{"run", "--rm",
		"--network", "none",
		"--memory", "128m",
		"--cpus", "0.5",
		"--pids-limit", "128",
		"--cap-drop", "ALL",
		"--read-only",
		"-v", dir + ":/app:ro",
		"-w", "/app",
		image,
	}
	dockerArgs = append(dockerArgs, cmd...)
	cmdExec := exec.CommandContext(ctx, "docker", dockerArgs...)

	start := time.Now()
	var stdout, stderr bytes.Buffer
	cmdExec.Stdout = &stdout
	cmdExec.Stderr = &stderr
	runErr := cmdExec.Run()
	elapsed := time.Since(start).Milliseconds()

	res := &Result{Stdout: trim(stdout.String()), Stderr: trim(stderr.String()), ElapsedMS: elapsed}
	if runErr != nil {
		exitCode := -1
		var ee *exec.ExitError
		if errors.As(runErr, &ee) {
			exitCode = ee.ExitCode()
		} else if ctx.Err() != nil {
			exitCode = 124
		}
		res.ExitCode = exitCode
	}
	return res, nil
}
