// Package sandbox compiles and runs user-submitted Go code.
// It uses a local executor process (exec, suited for local/intranet demos), with an optional Docker container backend for hardening.
package sandbox

import (
	"bytes"
	"context"
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// Hard runtime limits (server-side fallback; frontend params are not trusted).
const (
	maxTimeout = 5 * time.Second // max timeout per run; force-kill when reached
	buildLimit = 12 * time.Second
	maxOutput  = 1 << 20 // output truncation cap, 1MB
	maxCodeLen = 1 << 15 // source length cap, 32KB
)

// Result holds the output and stats of a single run.
type Result struct {
	Stdout    string `json:"stdout"`
	Stderr    string `json:"stderr"`
	ExitCode  int    `json:"exit_code"`
	ElapsedMS int64  `json:"elapsed_ms"`
}

// Runner abstracts over the different sandbox backends.
type Runner interface {
	Run(code, lang string, timeout time.Duration) (*Result, error)
}

// New creates a Runner by backend name: "docker" uses containers, otherwise local process execution.
func New(backend string) Runner {
	if strings.EqualFold(backend, "docker") {
		return &dockerRunner{}
	}
	return &execRunner{}
}

// execRunner executes locally: write a temp main.go (or main.py) then build & run within the time limit.
type execRunner struct{}

func (e *execRunner) Run(code, lang string, timeout time.Duration) (*Result, error) {
	if len(code) > maxCodeLen {
		return nil, errors.New("code too long")
	}
	if timeout <= 0 || timeout > maxTimeout {
		timeout = maxTimeout
	}

	dir, err := os.MkdirTemp("", "qcc-sandbox-*")
	if err != nil {
		return nil, err
	}
	defer os.RemoveAll(dir)

	if lang == "python" {
		return runPython(dir, code, timeout)
	}
	return runGo(dir, code, timeout)
}

// runPython writes main.py and runs it with python3 (no compile step needed).
func runPython(dir, code string, timeout time.Duration) (*Result, error) {
	mainPath := filepath.Join(dir, "main.py")
	if err := os.WriteFile(mainPath, []byte(code), 0o600); err != nil {
		return nil, err
	}

	start := time.Now()
	runCtx, cancelRun := context.WithTimeout(context.Background(), timeout)
	defer cancelRun()
	run := exec.CommandContext(runCtx, pythonBin(), mainPath)
	run.Dir = dir
	var stdout, stderr bytes.Buffer
	run.Stdout = &stdout
	run.Stderr = &stderr
	runErr := run.Run()
	elapsed := time.Since(start).Milliseconds()

	res := &Result{Stdout: trim(stdout.String()), Stderr: trim(stderr.String()), ElapsedMS: elapsed}
	if runErr != nil {
		res.ExitCode = exitCodeOf(runErr, runCtx)
	}
	return res, nil
}

// pythonBin returns the python interpreter to use for Python examples.
// PYTHON_BIN lets deployments point to a specific venv interpreter; defaults to python3 (on PATH).
func pythonBin() string {
	if p := os.Getenv("PYTHON_BIN"); p != "" {
		return p
	}
	return "python3"
}

// runGo writes main.go, compiles it, and runs the produced binary.
func runGo(dir, code string, timeout time.Duration) (*Result, error) {
	mainPath := filepath.Join(dir, "main.go")
	if err := os.WriteFile(mainPath, []byte(code), 0o600); err != nil {
		return nil, err
	}
	binPath := filepath.Join(dir, "app")

	buildCtx, cancelBuild := context.WithTimeout(context.Background(), buildLimit)
	defer cancelBuild()
	build := exec.CommandContext(buildCtx, "go", "build", "-o", binPath, mainPath)
	build.Dir = dir
	if out, err := build.CombinedOutput(); err != nil {
		return &Result{Stderr: trim(string(out)), ExitCode: 2}, nil // compile error
	}

	start := time.Now()
	runCtx, cancelRun := context.WithTimeout(context.Background(), timeout)
	defer cancelRun()
	run := exec.CommandContext(runCtx, binPath)
	run.Dir = dir
	var stdout, stderr bytes.Buffer
	run.Stdout = &stdout
	run.Stderr = &stderr
	runErr := run.Run()
	elapsed := time.Since(start).Milliseconds()

	res := &Result{Stdout: trim(stdout.String()), Stderr: trim(stderr.String()), ElapsedMS: elapsed}
	if runErr != nil {
		res.ExitCode = exitCodeOf(runErr, runCtx)
	}
	return res, nil
}

// exitCodeOf maps a run error to a stable exit code: -1 on unknown, 124 on timeout.
func exitCodeOf(runErr error, runCtx context.Context) int {
	exitCode := -1
	var ee *exec.ExitError
	if errors.As(runErr, &ee) {
		exitCode = ee.ExitCode()
	} else if runCtx.Err() != nil {
		exitCode = 124 // timeout
	}
	return exitCode
}

// trim truncates oversized output to avoid exhausting memory.
func trim(s string) string {
	if len(s) > maxOutput {
		return s[:maxOutput] + "\n...[truncated]"
	}
	return s
}
