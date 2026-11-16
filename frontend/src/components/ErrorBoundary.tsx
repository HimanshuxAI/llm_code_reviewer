import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * Catches render-time errors so a crash shows a readable message instead of
 * a blank white page. Without this, one bad property access anywhere in the
 * tree unmounts the whole app with no feedback.
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Unhandled UI error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen flex items-center justify-center p-8">
          <div className="panel p-10 max-w-lg text-center">
            <div className="empty-mark">!</div>
            <h1 className="empty-title">Something broke on this screen</h1>
            <p className="empty-sub">
              The page failed to render. Reloading usually fixes it. If it keeps
              happening, the error is below.
            </p>
            <pre className="issue-fix mt-6 text-left">
              {this.state.error.message}
            </pre>
            <div className="mt-6 flex gap-3 justify-center">
              <button
                onClick={() => window.location.reload()}
                className="btn btn-primary"
              >
                Reload page
              </button>
              <a href="/submit" className="btn btn-ghost">
                New review
              </a>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
