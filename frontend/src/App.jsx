import { useState } from 'react'
import './App.css'

const API_URL = 'https://sql-plan-visualizer-production.up.railway.app'

function severityColor(severity) {
  if (severity === 'high') return '#dc2626'
  if (severity === 'medium') return '#d97706'
  return '#6b7280'
}

function getPlanSummary(plan) {
  const root = plan[0]?.Plan
  if (!root) return null
  return {
    nodeType: root['Node Type'],
    executionTime: plan[0]['Execution Time'],
    planningTime: plan[0]['Planning Time'],
    actualRows: root['Actual Rows'],
    indexName: root['Index Name'] || null,
  }
}

function App() {
  const [sql, setSql] = useState("SELECT * FROM orders WHERE order_status = 'pending'")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  async function handleAnalyze() {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql }),
      })
      const data = await response.json()

      if (data.error) {
        setError(data.error)
      } else {
        setResult(data)
      }
    } catch (err) {
      setError('Could not reach the API. Is the backend server running?')
    } finally {
      setLoading(false)
    }
  }

  function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
  }

  const summary = result ? getPlanSummary(result.plan) : null

  return (
    <div className="app">
      <h1>SQL Query Plan Visualizer</h1>
      <p className="subtitle">
        Paste a query, see how Postgres actually executes it, and get suggested fixes.
      </p>

      <textarea
        className="sql-input"
        value={sql}
        onChange={(e) => setSql(e.target.value)}
        rows={5}
        placeholder="Paste your SQL query here..."
      />

      <button onClick={handleAnalyze} disabled={loading} className="analyze-btn">
        {loading ? (<><span className="spinner"></span>Analyzing...</>) : "Analyze Query"}
      </button>

      {error && (
        <div className="error-box">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && summary && (
        <div className="results">
          <div className="plan-summary">
            <div className="summary-item">
              <span className="summary-label">Execution time</span>
              <strong>{summary.executionTime?.toFixed(2)} ms</strong>
            </div>
            <div className="summary-item">
              <span className="summary-label">Planning time</span>
              <strong>{summary.planningTime?.toFixed(2)} ms</strong>
            </div>
            <div className="summary-item">
              <span className="summary-label">Rows returned</span>
              <strong>{summary.actualRows?.toLocaleString()}</strong>
            </div>
            <div className="summary-item">
              <span className="summary-label">Scan type</span>
              <strong>{summary.nodeType}</strong>
            </div>
            {summary.indexName && (
              <div className="summary-item">
                <span className="summary-label">Index used</span>
                <strong className="index-used">{summary.indexName}</strong>
              </div>
            )}
          </div>

          <h2>Issues Found ({result.issues.length})</h2>
          {result.issues.length === 0 && (
            <p className="no-issues">
              ✓ No issues detected.
              {summary.indexName
                ? ` Query used index "${summary.indexName}" efficiently.`
                : summary.nodeType === 'Seq Scan'
                ? ' Full table scan — acceptable if no filter was applied.'
                : ' This query looks efficient.'}
            </p>
          )}

          {result.issues.map((issue, idx) => (
            <div key={idx} className="issue-card" style={{ borderLeftColor: severityColor(issue.severity) }}>
              <div className="issue-header">
                <span className="severity-badge" style={{ backgroundColor: severityColor(issue.severity) }}>
                  {issue.severity}
                </span>
                <span className="issue-type">{issue.type}</span>
              </div>
              <p className="issue-message">{issue.message}</p>
              {issue.suggested_index && (
                <div className="suggested-index">
                  <code>{issue.suggested_index}</code>
                  <button className="copy-btn" onClick={() => copyToClipboard(issue.suggested_index)}>
                    Copy
                  </button>
                </div>
              )}
            </div>
          ))}

          <details className="raw-plan">
            <summary>View raw execution plan (JSON)</summary>
            <pre>{JSON.stringify(result.plan, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  )
}

export default App
