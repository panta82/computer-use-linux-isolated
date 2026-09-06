# Scope of isolation

This project separates normal model GUI input from the user's primary desktop. It runs under the same Unix account with access to the user's files. It does not contain malicious same-user code or prevent arbitrary launched applications from discovering other same-user processes. Do not use it as an untrusted-code sandbox.

Report problems through the fork's GitHub issues without including credentials, browser profiles, authentication files, or personal desktop screenshots. Never solve a startup failure by enabling host input, weakening AppArmor globally, or changing DISPLAY to the primary session.
