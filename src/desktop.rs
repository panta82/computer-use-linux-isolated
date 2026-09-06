use anyhow::{Context, Result};
use std::os::unix::process::CommandExt;

pub(crate) fn dispatch() -> Result<bool> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.is_empty() || matches!(args[0].as_str(), "--help" | "-h") {
        println!("computer-use-linux-isolated\n\n desktop install|start|stop|status|view|run PROGRAM [ARGS...]|uninstall\n mcp | doctor | setup | apps | state [APP] | windows | screenshot\n\nInstall native dependencies first: ./install.sh --dependencies");
        return Ok(true);
    }
    if std::env::var("COMPUTER_USE_LINUX_INTERNAL").as_deref() == Ok("1") && args[0] != "desktop" {
        return Ok(false);
    }
    let exe = std::env::current_exe().context("locate executable")?;
    let error = std::process::Command::new("/usr/bin/python3")
        .arg("-c")
        .arg(include_str!("../desktop/manage.py"))
        .env("CUL_SESSION_SOURCE", include_str!("../desktop/session.py"))
        .arg(exe)
        .args(args)
        .exec();
    Err(error).context("launch desktop manager")
}
