# Security Policy

## How to report

**Preferred:** [open a private security advisory](https://github.com/rktreddy/open-image-saver/security/advisories/new). This creates a private channel between you and the maintainer — nothing is public until the advisory is published.

**Alternative:** contact via the email on the maintainer's [GitHub profile](https://github.com/rktreddy) with `[SECURITY]` in the subject.

Please do **not** open a public issue for anything you believe is exploitable. If you're not sure, err private.

## Supported versions

| Version       | Supported |
|---------------|-----------|
| 1.x (latest)  | Yes       |
| Earlier 1.x   | No        |

The extension auto-updates through the Chrome Web Store, so most users stay on the latest version automatically.

## In scope

- Code in this repository — `background.js`, `offscreen.js`, `popup.js`, `manifest.json`
- Permission misuse: any path where the extension accesses data beyond the specific image the user right-clicked
- Supply-chain concerns about how releases are built and published to the Web Store
- Discrepancy between the `.zip` distributed via the Web Store and the source at the corresponding tag

## Out of scope

- Browser-level vulnerabilities (report to [Chromium](https://www.chromium.org/Home/chromium-security/reporting-security-bugs/))
- OS-level issues
- Bugs on third-party websites whose images you are saving
- Performance complaints — open a normal issue instead
- Social-engineering scenarios that require the user to install an unrelated malicious extension

## Response targets

Solo maintainer, volunteer time. Targets, not contractual promises:

- **Acknowledgement:** within 72 hours
- **Initial assessment:** within 7 days
- **Fix:** same-day or next-day for critical issues affecting users in the wild; next scheduled release otherwise

If something is being actively exploited and the maintainer is unreachable for more than 48 hours, escalating to a public issue tagged `urgent-security` is acceptable as a last resort.

## Maintainer commitments

The previous "Save Image as Type" extension was hijacked because its maintainer sold it. That is the primary threat model for an extension like this — far more likely than a clever code bug. To address it head-on:

1. **This project will not be sold.** Not the codebase, not the GitHub org, not the Chrome Web Store listing, not any signing keys, not the update channel. If anyone is offered money for any of those, the answer is no. Forks are welcome — clone the code, publish your own listing, earn your own trust. The existing install base does not transfer.
2. **No new permissions without a public release note that justifies them.** Adding `tabs`, `webRequest`, `scripting`, `cookies`, or similar requires opening a public issue first and explaining what feature actually requires the new permission.
3. **No runtime code loading.** The extension will never fetch and execute remote JavaScript or WebAssembly. What ships at a release tag is what runs in your browser.
4. **No telemetry, ever.** Not analytics, not error reporting, not crash dumps. A network call in a release that goes anywhere other than the image URL you right-clicked is a bug — report it.

## Verifying a release

Reproducible builds are planned for v1.0. Once that lands, each release will publish the SHA-256 of the distributed `.zip`. To verify:

1. Clone at the release tag.
2. Run the build script.
3. Compare your local `dist/*.zip` SHA-256 against the hash in the release notes.
4. Optionally: download the `.crx` from the Web Store, unpack the `.zip` inside, and compare against both.

A mismatch is a security finding — please report it via the channels above.

## Credit

Reporters are credited in release notes unless they prefer to remain anonymous. No bounty program — the credit is the thanks.
