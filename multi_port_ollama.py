#!/usr/bin/env python3
"""
Multi-Port Ollama Network - Run Multiple AI Models Simultaneously

The crazy vision: Run Ollama on different ports with different models/temperatures
to generate content variations in parallel, then pick the best one.

Like a slot machine where each reel is a different AI model spinning at the same time.

Port Strategy:
- 11434: llama3 (temp 0.7) - Balanced, technical
- 11435: mistral (temp 0.9) - Creative, engaging
- 11436: codellama (temp 0.5) - Precise, code-focused
- 11437: llama3 (temp 1.2) - Wild, experimental

Usage:
    from multi_port_ollama import MultiPortOllama

    tumbler = MultiPortOllama()

    # Generate on all ports simultaneously
    results = tumbler.generate_parallel(
        prompt="Write announcement for CringeProof game",
        ports=[11434, 11435, 11436, 11437]
    )

    # Returns 4 variations
    # Pick best one automatically
    best = tumbler.pick_best(results)
"""

import sys
import requests
import json
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# =============================================================================
# PORT CONFIGURATIONS
# =============================================================================

DEFAULT_PORTS = {
    11434: {"model": "llama3", "temperature": 0.7, "name": "Technical"},
    11435: {"model": "mistral", "temperature": 0.9, "name": "Creative"},
    11436: {"model": "codellama", "temperature": 0.5, "name": "Precise"},
    11437: {"model": "llama3", "temperature": 1.2, "name": "Experimental"}
}


# =============================================================================
# MULTI-PORT OLLAMA CLASS
# =============================================================================

class MultiPortOllama:
    """
    Manage multiple Ollama instances on different ports

    Think of this as the "tumbler engine" - spin multiple AI models
    at once and see which one produces the best output.
    """

    def __init__(self, port_configs: Optional[Dict] = None):
        """
        Initialize multi-port Ollama manager

        Args:
            port_configs: Custom port configurations (defaults to DEFAULT_PORTS)
        """
        self.ports = port_configs or DEFAULT_PORTS
        self.results_cache = {}

    def check_port_alive(self, port: int) -> bool:
        """
        Check if Ollama is running on a port

        Args:
            port: Port number

        Returns:
            True if alive, False otherwise
        """
        try:
            response = requests.get(f"http://localhost:{port}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def check_all_ports(self) -> Dict[int, bool]:
        """
        Check which ports are alive

        Returns:
            Dict of {port: is_alive}
        """
        status = {}
        for port in self.ports.keys():
            status[port] = self.check_port_alive(port)
        return status

    def generate_on_port(self, port: int, prompt: str,
                        system_prompt: Optional[str] = None) -> Dict:
        """
        Generate content on a specific port

        Args:
            port: Port number
            prompt: User prompt
            system_prompt: System prompt (optional)

        Returns:
            Dict with response, port, model, temperature
        """
        if port not in self.ports:
            return {
                "error": f"Port {port} not configured",
                "port": port
            }

        config = self.ports[port]

        # Build request payload
        payload = {
            "model": config["model"],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": config["temperature"]
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        # Make request
        try:
            start_time = time.time()

            response = requests.post(
                f"http://localhost:{port}/api/generate",
                json=payload,
                timeout=60
            )

            elapsed = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                return {
                    "port": port,
                    "model": config["model"],
                    "temperature": config["temperature"],
                    "name": config["name"],
                    "response": data.get("response", ""),
                    "elapsed_seconds": round(elapsed, 2),
                    "success": True
                }
            else:
                return {
                    "port": port,
                    "model": config["model"],
                    "error": f"HTTP {response.status_code}",
                    "success": False
                }

        except Exception as e:
            return {
                "port": port,
                "model": config["model"],
                "error": str(e),
                "success": False
            }

    def generate_parallel(self, prompt: str,
                         ports: Optional[List[int]] = None,
                         system_prompt: Optional[str] = None,
                         max_workers: int = 4) -> List[Dict]:
        """
        Generate content on multiple ports in parallel

        This is the TUMBLER - spin all the AI models at once!

        Args:
            prompt: User prompt
            ports: List of ports to use (defaults to all configured)
            system_prompt: System prompt (optional)
            max_workers: Max concurrent requests

        Returns:
            List of results from each port
        """
        if ports is None:
            ports = list(self.ports.keys())

        results = []

        # Use ThreadPoolExecutor to run in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_port = {
                executor.submit(
                    self.generate_on_port,
                    port,
                    prompt,
                    system_prompt
                ): port
                for port in ports
            }

            # Collect results as they complete
            for future in as_completed(future_to_port):
                port = future_to_port[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        "port": port,
                        "error": str(e),
                        "success": False
                    })

        # Cache results
        cache_key = f"{prompt}_{','.join(map(str, ports))}"
        self.results_cache[cache_key] = results

        return results

    def score_response(self, response: str) -> float:
        """
        Score a response quality (simple heuristic)

        Better scoring = higher number

        Factors:
        - Length (not too short, not too long)
        - Readability (sentences, paragraphs)
        - Markdown formatting
        - Code blocks (if applicable)

        Args:
            response: AI-generated text

        Returns:
            Score (0-100)
        """
        if not response:
            return 0.0

        score = 0.0

        # Length score (sweet spot: 200-1000 chars)
        length = len(response)
        if 200 <= length <= 1000:
            score += 30
        elif length > 1000:
            score += 20
        elif length > 100:
            score += 10

        # Sentence structure (periods, question marks)
        sentences = response.count('.') + response.count('?') + response.count('!')
        score += min(sentences * 3, 20)

        # Paragraphs (newlines)
        paragraphs = response.count('\n\n')
        score += min(paragraphs * 5, 15)

        # Markdown formatting
        if '**' in response or '__' in response:
            score += 10  # Bold
        if '#' in response:
            score += 10  # Headers
        if '```' in response:
            score += 15  # Code blocks

        # Lists
        if response.count('- ') > 2 or response.count('* ') > 2:
            score += 10

        return min(score, 100.0)

    def pick_best(self, results: List[Dict],
                  scoring_fn: Optional[callable] = None) -> Dict:
        """
        Pick the best response from multiple results

        Args:
            results: List of generation results
            scoring_fn: Custom scoring function (optional)

        Returns:
            Best result dict with added 'score' field
        """
        if not results:
            return {}

        # Filter out failures
        successful = [r for r in results if r.get("success")]

        if not successful:
            return {"error": "All ports failed"}

        # Score each result
        scoring_fn = scoring_fn or self.score_response

        for result in successful:
            result["score"] = scoring_fn(result.get("response", ""))

        # Pick highest score
        best = max(successful, key=lambda r: r["score"])

        return best

    def compare_results(self, results: List[Dict]) -> str:
        """
        Generate comparison report of all results

        Args:
            results: List of generation results

        Returns:
            Markdown-formatted comparison report
        """
        report = "# Multi-Port Ollama Comparison\n\n"

        # Summary table
        report += "## Summary\n\n"
        report += "| Port | Model | Temp | Status | Score | Time |\n"
        report += "|------|-------|------|--------|-------|------|\n"

        for result in results:
            port = result.get("port", "?")
            model = result.get("model", "?")
            temp = result.get("temperature", "?")
            status = "✅" if result.get("success") else "❌"
            score = f"{result.get('score', 0):.1f}" if result.get("score") else "N/A"
            elapsed = f"{result.get('elapsed_seconds', 0)}s" if result.get("elapsed_seconds") else "N/A"

            report += f"| {port} | {model} | {temp} | {status} | {score} | {elapsed} |\n"

        # Best result
        best = self.pick_best(results)
        if best and not best.get("error"):
            report += f"\n## Winner: Port {best['port']} ({best['name']})\n\n"
            report += f"**Score:** {best['score']:.1f}/100\n\n"
            report += f"**Response:**\n\n{best['response']}\n\n"

        # All responses
        report += "## All Responses\n\n"

        for result in results:
            if result.get("success"):
                port = result["port"]
                name = result.get("name", "Unknown")
                score = result.get("score", 0)

                report += f"### Port {port}: {name} (Score: {score:.1f})\n\n"
                report += f"{result['response']}\n\n"
                report += "---\n\n"

        return report


# =============================================================================
# CLI TESTING
# =============================================================================

def main():
    """Test the multi-port Ollama system"""
    import sys

    print("🎰 Multi-Port Ollama Tumbler\n")

    tumbler = MultiPortOllama()

    # Check which ports are alive
    print("Checking ports...")
    status = tumbler.check_all_ports()

    alive_ports = [port for port, is_alive in status.items() if is_alive]
    dead_ports = [port for port, is_alive in status.items() if not is_alive]

    print(f"\n✅ Alive: {alive_ports}")
    print(f"❌ Dead: {dead_ports}")

    if not alive_ports:
        print("\n⚠️  No Ollama instances running!")
        print("Start Ollama on different ports:")
        print("  OLLAMA_HOST=0.0.0.0:11434 ollama serve &")
        print("  OLLAMA_HOST=0.0.0.0:11435 ollama serve &")
        return 1

    # Test prompt
    test_prompt = "Write a 2-sentence announcement for CringeProof, an AI consciousness game"

    print(f"\n📝 Testing prompt: '{test_prompt}'\n")
    print("🎰 Spinning the tumbler...\n")

    # Generate on all alive ports
    results = tumbler.generate_parallel(test_prompt, ports=alive_ports)

    # Show comparison
    comparison = tumbler.compare_results(results)
    print(comparison)

    return 0


if __name__ == "__main__":
    sys.exit(main())
