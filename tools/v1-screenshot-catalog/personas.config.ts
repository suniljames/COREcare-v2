// Env-driven persona credentials. Reads at module load (not lazy) so missing
// vars surface at startup, not 30 seconds in.
//
// The locked persona vocabulary lives in docs/migration/README.md §Personas
// and is mirrored here. Persona slug ↔ canonical name ↔ env var mapping
// MUST stay in sync with docs/legacy/README.md §Persona vocabulary.

export interface Persona {
  slug: string;            // kebab-case directory name
  canonical: string;       // exact display name from the locked vocabulary
  username: string | null; // env-driven; null = persona skipped this run
  password: string | null;
}

interface PersonaSpec {
  slug: string;
  canonical: string;
  envPrefix: string;
}

// Order matches docs/migration/README.md §Personas. Client persona omitted
// — v1 has no Client portal (per Phase 0 INVESTIGATIONS.md, Client is an
// object-of-care, not a User).
const PERSONA_SPECS: PersonaSpec[] = [
  { slug: "super-admin",   canonical: "Super-Admin",   envPrefix: "V1_SUPER_ADMIN" },
  { slug: "agency-admin",  canonical: "Agency Admin",  envPrefix: "V1_AGENCY_ADMIN" },
  { slug: "care-manager",  canonical: "Care Manager",  envPrefix: "V1_CARE_MANAGER" },
  { slug: "caregiver",     canonical: "Caregiver",     envPrefix: "V1_CAREGIVER" },
  { slug: "family-member", canonical: "Family Member", envPrefix: "V1_FAMILY_MEMBER" },
];

function loadPersona(spec: PersonaSpec): Persona {
  const username = process.env[`${spec.envPrefix}_USERNAME`] || null;
  const password = process.env[`${spec.envPrefix}_PASSWORD`] || null;
  return {
    slug: spec.slug,
    canonical: spec.canonical,
    username: username && username.length > 0 ? username : null,
    password: password && password.length > 0 ? password : null,
  };
}

export const PERSONAS: Persona[] = PERSONA_SPECS.map(loadPersona);

// Filter to personas with both username + password set; the rest are skipped
// from the run with their reason logged to RUN-MANIFEST.md.
export const ACTIVE_PERSONAS: Persona[] = PERSONAS.filter(
  (p) => p.username !== null && p.password !== null,
);

export const SKIPPED_PERSONAS: Persona[] = PERSONAS.filter(
  (p) => p.username === null || p.password === null,
);
