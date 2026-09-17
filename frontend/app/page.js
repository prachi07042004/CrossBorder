export default function Home() {
  return (
    <main style={{ padding: "3rem", maxWidth: 640 }}>
      <h1>AI-Assisted Cross-Border Tax &amp; Compliance System</h1>
      <p>
        Phase 0 hello-world skeleton — this confirms the frontend container
        builds and serves correctly. The real dashboard (upload,
        classification review, tax &amp; DTAA summary, audit report) is not
        built yet; see <code>PROGRESS.md</code> for status.
      </p>
      <p>
        Backend health check:{" "}
        <a href="http://localhost:8000/health">http://localhost:8000/health</a>
      </p>
    </main>
  );
}
