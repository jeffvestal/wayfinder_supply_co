import { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
    })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-slate-800 rounded-xl p-6 border border-red-500/20">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">Something went wrong</h2>
                <p className="text-sm text-gray-400">An unexpected error occurred</p>
              </div>
            </div>
            
            {this.state.error && (
              <div className="mb-4 p-3 bg-slate-900 rounded-lg border border-slate-700">
                <p className="text-xs text-gray-500 mb-1">Error details:</p>
                <p className="text-sm text-red-400 font-mono break-all">
                  {this.state.error.message || 'Unknown error'}
                </p>
              </div>
            )}

            <button
              onClick={this.handleReset}
              className="w-full bg-primary hover:bg-primary-dark text-white px-4 py-3 rounded-lg transition-all flex items-center justify-center gap-2 font-medium"
            >
              <RefreshCw className="w-4 h-4" />
              Try Again
            </button>

            <p className="text-xs text-gray-500 mt-4 text-center">
              If this problem persists, please refresh the page
            </p>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

