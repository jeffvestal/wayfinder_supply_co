import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Settings,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertCircle,
  XCircle,
  RefreshCw,
  ExternalLink,
  Camera,
  Sparkles,
  Globe,
  ChevronDown,
  Info,
  Shield,
} from 'lucide-react'
import { api } from '../lib/api'
import type { SettingsStatus, VisionServiceStatus } from '../types'

interface SettingsPageProps {
  settingsStatus: SettingsStatus
  onStatusChange: (status: SettingsStatus) => void
}

function StatusBadge({ status }: { status: VisionServiceStatus }) {
  if (status === 'configured_ui') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-400">
        <CheckCircle2 className="w-3 h-3" />
        Configured (Settings)
      </span>
    )
  }
  if (status === 'configured_env') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/20 text-blue-400">
        <CheckCircle2 className="w-3 h-3" />
        Configured (Environment)
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-zinc-700/50 text-zinc-400">
      <XCircle className="w-3 h-3" />
      Not Configured
    </span>
  )
}

export function SettingsPage({ settingsStatus, onStatusChange }: SettingsPageProps) {
  const [jinaKey, setJinaKey] = useState('')
  const [gcpServiceAccountJson, setGcpServiceAccountJson] = useState('')
  const [showJinaKey, setShowJinaKey] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [vertexProjectIdOverride, setVertexProjectIdOverride] = useState('')
  const [vertexLocation, setVertexLocation] = useState('')
  const [saving, setSaving] = useState(false)
  const [testingJina, setTestingJina] = useState(false)
  const [testingVertex, setTestingVertex] = useState(false)
  const [testResult, setTestResult] = useState<{ service: string; success: boolean; message: string } | null>(null)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)
  const [showGcpPrereqs, setShowGcpPrereqs] = useState(false)

  useEffect(() => {
    refreshStatus()
  }, [])

  const refreshStatus = async () => {
    try {
      const status = await api.getSettingsStatus()
      onStatusChange(status)
    } catch (e) {
      console.error('Failed to refresh settings status:', e)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setSaveMessage(null)
    setTestResult(null)
    try {
      const settings: Record<string, string> = {}
      if (jinaKey.trim()) settings.JINA_API_KEY = jinaKey.trim()
      if (gcpServiceAccountJson.trim()) settings.GCP_SERVICE_ACCOUNT_JSON = gcpServiceAccountJson.trim()
      if (vertexProjectIdOverride.trim()) settings.VERTEX_PROJECT_ID = vertexProjectIdOverride.trim()
      if (vertexLocation.trim()) settings.VERTEX_LOCATION = vertexLocation.trim()

      if (Object.keys(settings).length === 0) {
        setSaveMessage('No changes to save')
        setSaving(false)
        return
      }

      const newStatus = await api.updateSettings(settings)
      onStatusChange(newStatus)
      setJinaKey('')
      setGcpServiceAccountJson('')
      setVertexProjectIdOverride('')
      setSaveMessage('Settings saved successfully')
    } catch (e) {
      setSaveMessage('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  const handleTestJina = async () => {
    setTestingJina(true)
    setTestResult(null)
    try {
      // Auto-save if key is in input
      if (jinaKey.trim()) {
        const newStatus = await api.updateSettings({ JINA_API_KEY: jinaKey.trim() })
        onStatusChange(newStatus)
        setJinaKey('')
      }
      const result = await api.testJinaConnection()
      setTestResult({ service: 'jina', ...result })
    } catch {
      setTestResult({ service: 'jina', success: false, message: 'Connection test failed' })
    } finally {
      setTestingJina(false)
    }
  }

  const handleTestVertex = async () => {
    setTestingVertex(true)
    setTestResult(null)
    try {
      // Auto-save any pending inputs first
      const settings: Record<string, string> = {}
      if (gcpServiceAccountJson.trim()) settings.GCP_SERVICE_ACCOUNT_JSON = gcpServiceAccountJson.trim()
      if (vertexProjectIdOverride.trim()) settings.VERTEX_PROJECT_ID = vertexProjectIdOverride.trim()
      if (vertexLocation.trim()) settings.VERTEX_LOCATION = vertexLocation.trim()
      if (Object.keys(settings).length > 0) {
        const newStatus = await api.updateSettings(settings)
        onStatusChange(newStatus)
        setGcpServiceAccountJson('')
        setVertexProjectIdOverride('')
      }
      const result = await api.testVertexConnection()
      setTestResult({ service: 'vertex', ...result })
    } catch {
      setTestResult({ service: 'vertex', success: false, message: 'Connection test failed' })
    } finally {
      setTestingVertex(false)
    }
  }

  const isConfigured = (status: VisionServiceStatus) => status !== 'not_configured'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="max-w-3xl mx-auto py-8 px-4"
    >
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Settings className="w-7 h-7 text-primary" />
          <h1 className="text-2xl font-bold">Vision Settings</h1>
        </div>
        <p className="text-zinc-400">
          Configure API credentials for AI vision features. Keys entered here are stored in memory only and reset when the backend restarts. For persistent configuration, use the <code className="text-zinc-300 bg-zinc-800 px-1 rounded">.env</code> file.
        </p>
      </div>

      {/* Service Status Overview */}
      <div className="glass rounded-xl p-5 mb-6 border border-white/10">
        <h2 className="text-lg font-semibold mb-4">Service Status</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="flex flex-col items-center p-4 rounded-lg bg-white/5">
            <Camera className="w-8 h-8 text-blue-400 mb-2" />
            <span className="text-sm font-medium mb-1">Jina VLM</span>
            <span className="text-xs text-zinc-400 mb-2">Image Analysis</span>
            <StatusBadge status={settingsStatus.jina_vlm} />
          </div>
          <div className="flex flex-col items-center p-4 rounded-lg bg-white/5">
            <Globe className="w-8 h-8 text-purple-400 mb-2" />
            <span className="text-sm font-medium mb-1">Vertex AI</span>
            <span className="text-xs text-zinc-400 mb-2">Grounding</span>
            <StatusBadge status={settingsStatus.vertex_ai} />
            {settingsStatus.vertex_project_id && (
              <span className="text-[10px] text-zinc-500 mt-1 font-mono">{settingsStatus.vertex_project_id}</span>
            )}
          </div>
          <div className="flex flex-col items-center p-4 rounded-lg bg-white/5">
            <Sparkles className="w-8 h-8 text-amber-400 mb-2" />
            <span className="text-sm font-medium mb-1">Imagen 3</span>
            <span className="text-xs text-zinc-400 mb-2">Preview Generation</span>
            <StatusBadge status={settingsStatus.imagen} />
          </div>
        </div>
      </div>

      {/* Feature availability note */}
      <div className="glass rounded-xl p-4 mb-6 border border-white/10">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
          <div className="text-sm text-zinc-300">
            <p className="font-medium text-zinc-200 mb-1">How features unlock:</p>
            <ul className="space-y-1 text-zinc-400">
              <li>
                <strong className="text-zinc-300">Jina key only</strong> &mdash; enables image upload + terrain-aware recommendations in Trip Planner
              </li>
              <li>
                <strong className="text-zinc-300">Jina + Vertex AI</strong> &mdash; adds real-time condition grounding + product-in-scene preview images
              </li>
              <li>
                <strong className="text-zinc-300">No keys</strong> &mdash; app works exactly as before (no vision UI shown)
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Jina VLM Configuration */}
      <div className="glass rounded-xl p-5 mb-6 border border-white/10">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Camera className="w-5 h-5 text-blue-400" />
              Jina VLM
            </h2>
            <p className="text-sm text-zinc-400 mt-1">
              Vision language model for terrain and conditions analysis
            </p>
          </div>
          <StatusBadge status={settingsStatus.jina_vlm} />
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1">API Key</label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type={showJinaKey ? 'text' : 'password'}
                  value={jinaKey}
                  onChange={(e) => setJinaKey(e.target.value)}
                  placeholder={isConfigured(settingsStatus.jina_vlm) ? '••••••••  (already configured)' : 'Enter Jina API key'}
                  className="w-full bg-zinc-800/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-primary/50 pr-10"
                />
                <button
                  onClick={() => setShowJinaKey(!showJinaKey)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                >
                  {showJinaKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <button
                onClick={handleTestJina}
                disabled={testingJina || (!isConfigured(settingsStatus.jina_vlm) && !jinaKey.trim())}
                className="px-3 py-2 text-sm rounded-lg bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                {testingJina ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Test'}
              </button>
            </div>
          </div>
          <p className="text-xs text-zinc-500">
            Get a free API key at{' '}
            <a href="https://jina.ai" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline inline-flex items-center gap-0.5">
              jina.ai <ExternalLink className="w-3 h-3" />
            </a>{' '}
            (10M free tokens)
          </p>
        </div>
      </div>

      {/* Vertex AI Configuration */}
      <div className="glass rounded-xl p-5 mb-6 border border-white/10">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Globe className="w-5 h-5 text-purple-400" />
              Vertex AI / Imagen 3
            </h2>
            <p className="text-sm text-zinc-400 mt-1">
              Gemini grounding + image generation (requires GCP project)
            </p>
          </div>
          <StatusBadge status={settingsStatus.vertex_ai} />
        </div>

        <div className="space-y-4">
          {/* Primary input: Service Account JSON */}
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1">
              Service Account JSON
              {settingsStatus.vertex_project_id && (
                <span className="ml-2 text-xs font-normal text-emerald-400">
                  Project: {settingsStatus.vertex_project_id}
                </span>
              )}
            </label>
            <textarea
              value={gcpServiceAccountJson}
              onChange={(e) => setGcpServiceAccountJson(e.target.value)}
              placeholder={
                isConfigured(settingsStatus.vertex_ai)
                  ? '(already configured — paste new JSON to replace)'
                  : 'Paste your GCP service account JSON here...'
              }
              rows={5}
              className="w-full bg-zinc-800/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-primary/50 font-mono"
            />
            <p className="text-xs text-zinc-500 mt-1">
              Paste the full contents of your service account key JSON file. The project ID will be auto-extracted.
            </p>
          </div>

          {/* GCP Prerequisites accordion */}
          <div className="bg-zinc-800/30 rounded-lg border border-white/5 overflow-hidden">
            <button
              onClick={() => setShowGcpPrereqs(!showGcpPrereqs)}
              className="w-full flex items-center justify-between p-3 text-left hover:bg-white/5 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-amber-400" />
                <span className="text-xs font-medium text-zinc-300">GCP Prerequisites & Required Permissions</span>
              </div>
              <ChevronDown className={`w-4 h-4 text-zinc-400 transition-transform ${showGcpPrereqs ? 'rotate-180' : ''}`} />
            </button>
            <AnimatePresence>
              {showGcpPrereqs && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="px-3 pb-3 space-y-3 text-xs text-zinc-400">
                    <div>
                      <p className="font-medium text-zinc-300 mb-1">1. Enable these APIs in your GCP project:</p>
                      <ul className="list-disc list-inside space-y-0.5 ml-1">
                        <li><code className="bg-zinc-800 px-1 rounded">Vertex AI API</code> (aiplatform.googleapis.com)</li>
                        <li><code className="bg-zinc-800 px-1 rounded">Cloud AI Platform API</code> (for Imagen)</li>
                      </ul>
                    </div>
                    <div>
                      <p className="font-medium text-zinc-300 mb-1">2. Service account IAM role (minimum):</p>
                      <ul className="list-disc list-inside space-y-0.5 ml-1">
                        <li><code className="bg-zinc-800 px-1 rounded">Vertex AI User</code> (roles/aiplatform.user)</li>
                      </ul>
                    </div>
                    <div>
                      <p className="font-medium text-zinc-300 mb-1">3. Create a JSON key for the service account:</p>
                      <p className="ml-1">
                        GCP Console → IAM & Admin → Service Accounts → Keys → Add Key → JSON
                      </p>
                    </div>
                    <div className="pt-1 border-t border-white/5">
                      <p className="text-zinc-500">
                        The app uses the <code className="bg-zinc-800 px-0.5 rounded">cloud-platform</code> OAuth scope internally. Your service account&apos;s IAM role controls what actions are allowed within that scope.
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Advanced section: manual overrides */}
          <div className="bg-zinc-800/30 rounded-lg border border-white/5 overflow-hidden">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="w-full flex items-center justify-between p-3 text-left hover:bg-white/5 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Info className="w-4 h-4 text-zinc-400" />
                <span className="text-xs font-medium text-zinc-300">Advanced: Override Project ID & Location</span>
              </div>
              <ChevronDown className={`w-4 h-4 text-zinc-400 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
            </button>
            <AnimatePresence>
              {showAdvanced && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="px-3 pb-3 space-y-3">
                    <p className="text-xs text-zinc-500">
                      These are auto-extracted from the service account JSON. Override only if you need to use a different project or region.
                    </p>
                    <div>
                      <label className="block text-xs font-medium text-zinc-400 mb-1">Project ID Override</label>
                      <input
                        type="text"
                        value={vertexProjectIdOverride}
                        onChange={(e) => setVertexProjectIdOverride(e.target.value)}
                        placeholder={settingsStatus.vertex_project_id || 'Auto-extracted from JSON'}
                        className="w-full bg-zinc-900/50 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-primary/50"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-zinc-400 mb-1">Location</label>
                      <input
                        type="text"
                        value={vertexLocation}
                        onChange={(e) => setVertexLocation(e.target.value)}
                        placeholder="us-central1 (default)"
                        className="w-full bg-zinc-900/50 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-primary/50"
                      />
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Test button */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleTestVertex}
              disabled={testingVertex || (!isConfigured(settingsStatus.vertex_ai) && !gcpServiceAccountJson.trim() && !vertexProjectIdOverride.trim())}
              className="px-3 py-2 text-sm rounded-lg bg-purple-600/20 text-purple-400 hover:bg-purple-600/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
            >
              {testingVertex ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Test Connection'}
            </button>
            <p className="text-xs text-zinc-500">
              Alternatively, set <code className="bg-zinc-800 px-1 rounded">GOOGLE_APPLICATION_CREDENTIALS</code> + <code className="bg-zinc-800 px-1 rounded">VERTEX_PROJECT_ID</code> in <code className="bg-zinc-800 px-1 rounded">.env</code> for persistent Docker deployments.
            </p>
          </div>
        </div>
      </div>

      {/* Test Result */}
      {testResult && (
        <div
          className={`rounded-xl p-4 mb-6 border ${
            testResult.success
              ? 'bg-emerald-500/10 border-emerald-500/30'
              : 'bg-red-500/10 border-red-500/30'
          }`}
        >
          <div className="flex items-center gap-2">
            {testResult.success ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            ) : (
              <XCircle className="w-5 h-5 text-red-400" />
            )}
            <span className={testResult.success ? 'text-emerald-300' : 'text-red-300'}>
              {testResult.message}
            </span>
          </div>
        </div>
      )}

      {/* Save Message */}
      {saveMessage && (
        <div className="rounded-xl p-4 mb-6 border bg-blue-500/10 border-blue-500/30">
          <span className="text-blue-300">{saveMessage}</span>
        </div>
      )}

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2.5 rounded-lg bg-primary/20 text-primary hover:bg-primary/30 font-medium transition-all disabled:opacity-50 flex items-center gap-2"
        >
          {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : null}
          Save Settings
        </button>
      </div>
    </motion.div>
  )
}
