"use client";

import { useEffect, useMemo, useState } from "react";

type Profile = {
  full_name: string | null;
  headline: string | null;
  summary: string | null;
  target_titles: string[];
  skills: string[];
  technologies: string[];
  certifications: string[];
  education: string[];
  languages: string[];
  industries: string[];
  preferred_locations: string[];
  preferred_countries: string[];
  workplace_types: string[];
  employment_types: string[];
  seniority: string[];
  preferred_companies: string[];
  excluded_companies: string[];
  excluded_keywords: string[];
  min_salary: string | null;
  salary_currency: string | null;
  years_experience: string | null;
  willing_to_relocate: boolean;
};

type ProfileResponse = {
  exists: boolean;
  profile: Profile;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const emptyProfile: Profile = {
  full_name: "",
  headline: "",
  summary: "",
  target_titles: [],
  skills: [],
  technologies: [],
  certifications: [],
  education: [],
  languages: [],
  industries: [],
  preferred_locations: [],
  preferred_countries: [],
  workplace_types: [],
  employment_types: [],
  seniority: [],
  preferred_companies: [],
  excluded_companies: [],
  excluded_keywords: [],
  min_salary: "",
  salary_currency: "",
  years_experience: "",
  willing_to_relocate: false,
};

function parseList(value: string) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function listToText(value: string[]) {
  return value.join(", ");
}

async function getProfile(): Promise<ProfileResponse> {
  const response = await fetch(API_URL + "/api/v1/profile", { cache: "no-store" });
  if (!response.ok) throw new Error("API " + response.status);
  return response.json() as Promise<ProfileResponse>;
}

async function saveProfile(profile: Profile) {
  const response = await fetch(API_URL + "/api/v1/profile", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...profile,
      min_salary: profile.min_salary || null,
      salary_currency: profile.salary_currency || null,
      years_experience: profile.years_experience || null,
    }),
  });
  if (!response.ok) throw new Error("API " + response.status);
  return response.json();
}

export default function CandidateProfileClient() {
  const [profile, setProfile] = useState<Profile>(emptyProfile);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    let active = true;
    getProfile()
      .then((data) => {
        if (active) setProfile(data.profile);
      })
      .catch(() => {
        if (active) setMessage("Profile could not be loaded.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const listFields = useMemo(
    () =>
      [
        ["target_titles", "Target titles"],
        ["skills", "Skills"],
        ["technologies", "Technologies"],
        ["industries", "Industries"],
        ["preferred_locations", "Preferred locations"],
        ["preferred_countries", "Preferred countries"],
        ["workplace_types", "Workplace types"],
        ["employment_types", "Employment types"],
        ["seniority", "Seniority"],
        ["preferred_companies", "Preferred companies"],
        ["excluded_companies", "Excluded companies"],
        ["excluded_keywords", "Excluded keywords"],
        ["certifications", "Certifications"],
        ["education", "Education"],
        ["languages", "Languages"],
      ] as const,
    [],
  );

  function setListField(key: keyof Profile, value: string) {
    setProfile((current) => ({ ...current, [key]: parseList(value) }));
  }

  async function handleSave() {
    setSaving(true);
    setMessage("");
    try {
      await saveProfile(profile);
      setMessage("Profile saved.");
    } catch {
      setMessage("Profile could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="panel profile-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Candidate</span>
          <h2>Your profile</h2>
        </div>
        <span className="status">{loading ? "Loading" : "Editable"}</span>
      </div>

      {loading ? (
        <div className="empty-state">Loading candidate profile…</div>
      ) : (
        <>
          <div className="profile-grid">
            <label>
              Full name
              <input
                value={profile.full_name ?? ""}
                onChange={(event) => setProfile({ ...profile, full_name: event.target.value })}
              />
            </label>
            <label>
              Headline
              <input
                value={profile.headline ?? ""}
                onChange={(event) => setProfile({ ...profile, headline: event.target.value })}
              />
            </label>
            <label className="profile-wide">
              Summary
              <textarea
                rows={4}
                value={profile.summary ?? ""}
                onChange={(event) => setProfile({ ...profile, summary: event.target.value })}
              />
            </label>
            {listFields.map(([key, label]) => (
              <label key={key}>
                {label}
                <input
                  value={listToText(profile[key] as string[])}
                  placeholder="Separate values with commas"
                  onChange={(event) => setListField(key, event.target.value)}
                />
              </label>
            ))}
            <label>
              Minimum salary
              <input
                inputMode="decimal"
                value={profile.min_salary ?? ""}
                onChange={(event) => setProfile({ ...profile, min_salary: event.target.value })}
              />
            </label>
            <label>
              Salary currency
              <input
                maxLength={3}
                placeholder="CZK"
                value={profile.salary_currency ?? ""}
                onChange={(event) =>
                  setProfile({ ...profile, salary_currency: event.target.value.toUpperCase() })
                }
              />
            </label>
            <label>
              Years of experience
              <input
                inputMode="decimal"
                value={profile.years_experience ?? ""}
                onChange={(event) =>
                  setProfile({ ...profile, years_experience: event.target.value })
                }
              />
            </label>
            <label className="checkbox-field">
              <input
                type="checkbox"
                checked={profile.willing_to_relocate}
                onChange={(event) =>
                  setProfile({ ...profile, willing_to_relocate: event.target.checked })
                }
              />
              Willing to relocate
            </label>
          </div>

          <div className="profile-actions">
            <button className="refresh-button" onClick={() => void handleSave()} disabled={saving}>
              {saving ? "Saving…" : "Save profile"}
            </button>
            {message ? <span className="save-message">{message}</span> : null}
          </div>
        </>
      )}
    </section>
  );
}
