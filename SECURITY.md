# Security Policy

## Reporting a vulnerability

Please do not open a public issue for a security problem.

Report it privately through
[GitHub Security Advisories](https://github.com/RashadAnsari/KortingKlok/security/advisories/new).
Include the affected component, steps to reproduce, and the impact you expect.

You will get an acknowledgement within a few days. Once a fix is available, the
advisory is published with credit to the reporter unless you prefer otherwise.

## Supported versions

Fixes land on `master`. There are no maintained release branches.

## Running your own instance

This repository ships no credentials. Anyone running their own instance is
responsible for the secrets it needs:

- `DJANGO_SECRET_KEY` must be random and unique per deployment. The default in
  `.env.example` is for local development only.
- The Firebase service account JSON (`GOOGLE_APPLICATION_CREDENTIALS`) grants
  full access to your Firebase project. Keep it out of version control, out of
  container images, and mount it read-only.
- The Firebase client configuration in the app (`google-services.json`,
  `GoogleService-Info.plist`, `firebase_options.dart`) is generated per project
  and gitignored. Generate your own with `make firebase`.
- Android signing keys belong in `mobile/android/key.properties`, which is
  gitignored. Never commit a keystore.
- `ALLOWED_HOSTS` is permissive by default. Restrict it before exposing the API,
  and terminate TLS in front of it.
