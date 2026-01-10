#!/usr/bin/env node
/**
 * GoDaddy DNS Automation for GitHub Pages
 *
 * Updates DNS A records to point to GitHub Pages IPs
 * Official GoDaddy API - no web scraping needed
 *
 * Setup:
 *   1. Get API key: https://developer.godaddy.com/keys
 *   2. npm install axios
 *   3. export GODADDY_API_KEY="your_key"
 *   4. export GODADDY_API_SECRET="your_secret"
 *   5. node godaddy-dns-automation.js cringeproof.com soulfra.github.io
 */

const axios = require('axios');

const GITHUB_PAGES_IPS = [
  '185.199.108.153',
  '185.199.109.153',
  '185.199.110.153',
  '185.199.111.153'
];

class GoDaddyDNSAutomation {
  constructor(apiKey, apiSecret) {
    this.apiKey = apiKey;
    this.apiSecret = apiSecret;
    this.baseURL = 'https://api.godaddy.com/v1';
    this.headers = {
      'Authorization': `sso-key ${apiKey}:${apiSecret}`,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Update domain to point to GitHub Pages
   */
  async setupGitHubPages(domain, githubPagesUrl) {
    console.log(`\n🔧 Setting up ${domain} → ${githubPagesUrl}\n`);

    try {
      // 1. Get current DNS records
      console.log('📋 Fetching current DNS records...');
      const current = await this.getDNSRecords(domain);
      console.log(`   Found ${current.length} existing records`);

      // 2. Delete old A records
      console.log('\n🗑️  Deleting old A records...');
      await this.deleteARecords(domain);
      console.log('   ✅ Old A records removed');

      // 3. Add GitHub Pages A records
      console.log('\n➕ Adding GitHub Pages A records...');
      await this.addGitHubPagesARecords(domain);
      console.log('   ✅ Added 4 A records pointing to GitHub Pages');

      // 4. Update/Add CNAME for www
      console.log('\n🔗 Setting up www CNAME...');
      await this.addCNAME(domain, 'www', githubPagesUrl);
      console.log(`   ✅ www.${domain} → ${githubPagesUrl}`);

      // 5. Verify changes
      console.log('\n✅ DNS Update Complete!\n');
      console.log('Next steps:');
      console.log(`1. Wait 5-30 minutes for DNS propagation`);
      console.log(`2. Check: dig ${domain} +short`);
      console.log(`3. Visit: https://${domain}`);
      console.log(`4. GitHub will auto-enable HTTPS (may take 24hrs)\n`);

      return true;

    } catch (error) {
      console.error(`\n❌ Error: ${error.message}`);
      if (error.response) {
        console.error(`   API Response: ${JSON.stringify(error.response.data)}`);
      }
      return false;
    }
  }

  /**
   * Get all DNS records for domain
   */
  async getDNSRecords(domain) {
    const response = await axios.get(
      `${this.baseURL}/domains/${domain}/records`,
      { headers: this.headers }
    );
    return response.data;
  }

  /**
   * Delete all A records
   */
  async deleteARecords(domain) {
    try {
      await axios.delete(
        `${this.baseURL}/domains/${domain}/records/A/@`,
        { headers: this.headers }
      );
    } catch (error) {
      // Ignore if no A records exist
      if (error.response?.status !== 404) {
        throw error;
      }
    }
  }

  /**
   * Add GitHub Pages A records
   */
  async addGitHubPagesARecords(domain) {
    const aRecords = GITHUB_PAGES_IPS.map(ip => ({
      type: 'A',
      name: '@',
      data: ip,
      ttl: 3600
    }));

    await axios.patch(
      `${this.baseURL}/domains/${domain}/records`,
      aRecords,
      { headers: this.headers }
    );
  }

  /**
   * Add/Update CNAME record
   */
  async addCNAME(domain, name, value) {
    await axios.put(
      `${this.baseURL}/domains/${domain}/records/CNAME/${name}`,
      [{ type: 'CNAME', name, data: value, ttl: 3600 }],
      { headers: this.headers }
    );
  }

  /**
   * Batch update multiple domains
   */
  async setupMultipleDomains(domainMappings) {
    console.log(`\n📦 Batch updating ${domainMappings.length} domains...\n`);

    const results = [];

    for (const { domain, githubPagesUrl } of domainMappings) {
      const success = await this.setupGitHubPages(domain, githubPagesUrl);
      results.push({ domain, success });

      // Rate limit: wait 1 second between requests
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    console.log('\n📊 Batch Update Results:');
    results.forEach(({ domain, success }) => {
      console.log(`   ${success ? '✅' : '❌'} ${domain}`);
    });

    return results;
  }
}

// CLI Usage
if (require.main === module) {
  const apiKey = process.env.GODADDY_API_KEY;
  const apiSecret = process.env.GODADDY_API_SECRET;

  if (!apiKey || !apiSecret) {
    console.error('❌ Missing GoDaddy API credentials!');
    console.error('\nGet your API key at: https://developer.godaddy.com/keys');
    console.error('\nThen run:');
    console.error('  export GODADDY_API_KEY="your_key_here"');
    console.error('  export GODADDY_API_SECRET="your_secret_here"');
    console.error('  node godaddy-dns-automation.js cringeproof.com soulfra.github.io\n');
    process.exit(1);
  }

  const domain = process.argv[2];
  const githubPagesUrl = process.argv[3];

  if (!domain || !githubPagesUrl) {
    console.error('Usage: node godaddy-dns-automation.js <domain> <github-pages-url>');
    console.error('Example: node godaddy-dns-automation.js cringeproof.com soulfra.github.io');
    process.exit(1);
  }

  const automation = new GoDaddyDNSAutomation(apiKey, apiSecret);
  automation.setupGitHubPages(domain, githubPagesUrl);
}

module.exports = GoDaddyDNSAutomation;
