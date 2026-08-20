# Security Policy

## Supported versions

Oráculo is currently an early-stage project. Security fixes target the latest code on the default branch until versioned releases define a broader support policy.

## Reporting a vulnerability

Do not publish exploitable vulnerabilities, secrets or private datasets in a public Issue. Use GitHub's private vulnerability reporting feature when it is available for the repository. If no private channel is configured, open a public Issue containing only a request for a private contact method, without technical exploit details.

Include, through the private channel:

- affected version or commit;
- impact and prerequisites;
- minimal reproduction steps;
- suggested mitigation, if known;
- whether secrets or user data may have been exposed.

## Security model

The current release is local-first and single-user. It has no multi-user authentication and must bind to `127.0.0.1` by default. Do not expose it directly to a LAN or the internet without authentication, TLS, firewall rules and an explicit threat review.

Sensitive local artifacts include:

- `.env.local` and API credentials;
- SQLite databases, WAL and SHM files;
- backups and state exports;
- prompts or logs containing selected user context.

These files must not be committed or attached to Issues. The public `.env.example` must contain placeholders only.

## External AI boundary

Local CRUD does not require an external model. When AI or web research is enabled, selected context may leave the machine. Users must be able to inspect the relevant context and remain responsible for provider terms, retention settings, cost and data sensitivity.

Consequential actions such as purchases, messages, account changes or publishing require explicit human confirmation. A model recommendation is never authorization.

## Backup limitations

Backups are not encrypted at rest by the application. Store them with operating-system access controls, verify the target installation before restoration and never restore over an open database.
