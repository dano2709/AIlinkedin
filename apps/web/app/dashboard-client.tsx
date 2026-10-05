"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import CandidateProfileClient from "./candidate-profile-client";

type Overview = {
  total_jobs: number;
  active_jobs: number;
  remote_jobs: number;
  new_jobs_24h: number;
  companies: number;
  searches: number;
};

type Job = {
  id: string;
  title: string;
  company_name: string | null;
  location: string | null;
  workplace_type: string;
  employment_type: string | null;
  experience_level: string | null;
  salary_min: string | null;
  salary_max: string | null;
  salary_currency: string | null;
  job_state: string;
  applicant_count: number | null;
  external_apply_url: string | null;
  apply_url: string | null;
  ats_provider: string | null;
  posted_at: string | null;
  discovered_at: string;
};

type JobsResponse = {
  total: number;
  offset: number;
  limit: number;
  jobs: Job[];
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function formatSalary(job: Job) {
  if (!job.salary_min && !job.salary_max) return "—";
  const currency = job.salary_currency ? ` ${job.salary_currency}` : "";
  if (job.salary_min === job.salary_max) return `${job.salary_min}${currency}`;
  return `${job.salary_min ?? "?"}–${job.salary_max ?? "?"}${currency}`;
}

function formatDate(value: string | null) {
  if (!value) return "Unknown";
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function titleCase(value: string) {
  return value.toLowerCase().replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(API_URL + path, { cache: "no-store" });
  if (!response.ok) throw new Error(`API ${response.status}`);
  return response.json() as Promise<T>;
}

export default function DashboardClient() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [jobs, setJobs] = useState<JobsResponse | null>(null);
  const [query, setQuery] = useState("");
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const jobQuery = useMemo(() => {
    const params = new URLSearchParams();
    params.set("limit", "50");
    if (query.trim()) params.set("query", query.trim());
    if (remoteOnly) params.set("remote_only", "true");
    return params.toString();
  }, [query, remoteOnly]);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const [overviewData, jobsData] = await Promise.all([
        getJson<Overview>("/api/v1/dashboard/overview"),
        getJson<JobsResponse>("/api/v1/dashboard/jobs?" + jobQuery),
      ]);
      setOverview(overviewData);
      setJobs(jobsData);
    } catch {
      setError("Dashboard API is unavailable. Start the API and refresh.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [jobQuery]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <main>
      <header className="hero dashboard-hero">
        <div>
          <span className="eyebrow">AIlinkedin / Dashboard</span>
          <h1>Job Intelligence</h1>
          <p>Live view of discovered LinkedIn jobs, companies and recent activity.</p>
        </div>
        <button className="refresh-button" onClick={() => void refresh()} disabled={refreshing}>
          {refreshing ? "Refreshing…" : "Refresh"}
        </button>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="stats" aria-label="Dashboard overview">
        {[
          ["Jobs", overview?.total_jobs ?? 0, "All canonical jobs"],
          ["Active", overview?.active_jobs ?? 0, "Currently listed"],
          ["Remote", overview?.remote_jobs ?? 0, "Remote opportunities"],
          ["New 24h", overview?.new_jobs_24h ?? 0, "Recently discovered"],
          ["Companies", overview?.companies ?? 0, "Unique companies"],
          ["Searches", overview?.searches ?? 0, "Configured searches"],
        ].map(([label, value, hint]) => (
          <article className="card" key={String(label)}>
            <span>{label}</span>
            <strong>{loading ? "…" : value}</strong>
            <small>{hint}</small>
          </article>
        ))}
      </section>

      <section className="panel jobs-panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">Inventory</span>
            <h2>Discovered jobs</h2>
          </div>
          <span className="status">{jobs?.total ?? 0} total</span>
        </div>

        <div className="toolbar">
          <input
            aria-label="Search jobs"
            placeholder="Search title or company…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <label className="toggle">
            <input
              type="checkbox"
              checked={remoteOnly}
              onChange={(event) => setRemoteOnly(event.target.checked)}
            />
            Remote only
          </label>
        </div>

        {loading ? (
          <div className="empty-state">Loading dashboard data…</div>
        ) : jobs && jobs.jobs.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Role</th>
                  <th>Company</th>
                  <th>Location</th>
                  <th>Workplace</th>
                  <th>Salary</th>
                  <th>Applicants</th>
                  <th>Discovered</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {jobs.jobs.map((job) => (
                  <tr key={job.id}>
                    <td>
                      <strong>{job.title}</strong>
                      <small>{job.experience_level ?? "Experience not provided"}</small>
                    </td>
                    <td>{job.company_name ?? "Unknown company"}</td>
                    <td>{job.location ?? "Location not provided"}</td>
                    <td><span className="pill">{titleCase(job.workplace_type)}</span></td>
                    <td>{formatSalary(job)}</td>
                    <td>{job.applicant_count ?? "—"}</td>
                    <td>{formatDate(job.discovered_at)}</td>
                    <td>
                      {job.external_apply_url || job.apply_url ? (
                        <a
                          className="table-link"
                          href={job.external_apply_url || job.apply_url || "#"}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Apply
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <strong>No jobs yet.</strong>
            <span>Run a search and import a job to populate the dashboard.</span>
          </div>
        )}
      </section>

      <CandidateProfileClient />

      <section className="panel pipeline-panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">Pipeline</span>
            <h2>Processing status</h2>
          </div>
          <span className="status">Phase 6</span>
        </div>
        <div className="pipeline">
          {["Search", "Discover", "Normalize", "Persist", "Filter", "Analyze", "Rank"].map(
            (stage, index) => (
              <div className="stage" key={stage}>
                <span className="stage-index">{String(index + 1).padStart(2, "0")}</span>
                <span>{stage}</span>
              </div>
            ),
          )}
        </div>
      </section>
    </main>
  );
}
