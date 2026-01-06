use clap::Parser;
use rmcp::ServiceExt;

mod verus;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Path to the Verus binary
    #[arg(long, default_value = "verus")]
    verus_path: String,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    env_logger::init();
    let args = Args::parse();

    log::info!("Starting Verus MCP server via stdio");
    
    // Create the server with Verus tools
    let server = verus::VerusServer::new(args.verus_path);
    
    // Serve over stdio
    let transport = rmcp::transport::io::stdio();
    let peer = server.serve(transport).await?;
    
    log::info!("Server initialized, waiting for requests");
    peer.waiting().await?;
    
    Ok(())
}