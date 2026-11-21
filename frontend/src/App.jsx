import { useState } from 'react'
import './App.css'

const API_URL = 'https://sql-plan-visualizer-nwcr.vercel.app'
const REPO_URL = 'https://github.com/damarisnteseng-bot/SQL-PLAN-VISUALIZER'

const EXAMPLES = [
  { label: "Slow: full table scan", sql: "SELECT * FROM orders WHERE order_status = 'pending'" },
  { label: "Slow + index suggestion", sql: "SELECT * FROM order_items WHERE quantity > 4" },
  { label: "Fast: stops early", sql: "SELECT order_id FROM orders LIMIT 10" }
]

const TABLES = [
  { name: "customers", columns: "customer_id, full_name, email, city, country, created_at", rows: "about 6,000 rows" },
  { name: "products", columns: "product_id, product_name, category, price", rows: "about 250 rows" },
  { name: "orders", columns: "order_id, customer_id, order_status, order_date", rows: "100,000 rows" },
  { name: "order_items", columns: "order_item_id, order_id, product_id, quantity, unit_price", rows: "100,000 rows" }
]

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

      <div className="examples">
        <span className="examples-label">Try an example:</span>
        {EXAMPLES.map((ex) => (
          <button key={ex.label} className="example-btn" onClick={() => setSql(ex.sql)}>
            {ex.label}
          </button>
        ))}
      </div>

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

      <p className="demo-note">
        This demo accepts a single SELECT query and runs on a read-only database. The first request can take a few seconds to wake up.
      </p>

      <details className="schema-box">
        <summary>What tables can I query?</summary>
        {TABLES.map((t) => (
          <div key={t.name} className="schema-table">
            <strong>{t.name}</strong> <span className="schema-rows">({t.rows})</span>
            <div className="schema-columns">{t.columns}</div>
          </div>
        ))}
      </details>

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
              No issues detected.
              {summary.indexName
                ? ` Query used index "${summary.indexName}" efficiently.`
                : summary.nodeType === 'Seq Scan'
                ? ' Full table scan, which is acceptable if no filter was applied.'
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

      <footer className="site-footer">
        Built by Damaris Nteseng ·{' '}
        <a href={REPO_URL} target="_blank" rel="noreferrer">View the code on GitHub</a>
      </footer>
    </div>
  )
}

export default App
