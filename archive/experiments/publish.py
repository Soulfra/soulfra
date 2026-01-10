#!/usr/bin/env python3
"""
Neural Network Publishing Toolkit - "Git for AI"

Export, import, version control, and share trained neural networks.
Like git but for machine learning models!

Usage:
    # Export a network
    python3 publish.py export color_classifier --format json

    # Import someone else's network
    python3 publish.py import network_package.tar.gz

    # Create a shareable package
    python3 publish.py package color_classifier --output my_network.tar.gz

    # Diff two network versions
    python3 publish.py diff color_classifier color_classifier_v2

    # List all networks
    python3 publish.py list

Philosophy:
-----------
Neural networks should be:
1. Shareable - Export and import easily
2. Versionable - Track changes over time
3. Forkable - Build on others' work
4. Transparent - Understand what changed

ZERO external dependencies - just Python stdlib!
"""

import json
import sqlite3
import os
import sys
import tarfile
import gzip
import hashlib
from datetime import datetime
from pathlib import Path
import struct


class NeuralNetworkPublisher:
    """Publish, export, import, and version neural networks"""

    def __init__(self, db_path='soulfra.db'):
        self.db_path = db_path

    # ========================================================================
    # 1. EXPORT NETWORKS
    # ========================================================================

    def export_network(self, model_name, output_format='json', output_file=None):
        """
        Export a trained neural network to a file

        Args:
            model_name: Name of the network in the database
            output_format: 'json', 'binary', 'python', 'numpy_compat'
            output_file: Optional output filename

        Returns:
            Path to exported file
        """
        # Fetch network from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM neural_networks WHERE model_name = ?', (model_name,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError(f"Network '{model_name}' not found in database")

        # Parse row
        network_data = {
            'id': row[0],
            'model_name': row[1],
            'description': row[2],
            'input_size': row[3],
            'hidden_sizes': json.loads(row[4]) if row[4] else [],
            'output_size': row[5],
            'model_data': json.loads(row[6]) if row[6] else {},
            'trained_at': row[7]
        }

        # Export in requested format
        if output_format == 'json':
            return self._export_json(network_data, output_file)
        elif output_format == 'binary':
            return self._export_binary(network_data, output_file)
        elif output_format == 'python':
            return self._export_python(network_data, output_file)
        elif output_format == 'numpy_compat':
            return self._export_numpy_compat(network_data, output_file)
        else:
            raise ValueError(f"Unknown format: {output_format}")

    def _export_json(self, network_data, output_file=None):
        """Export as JSON (human-readable, editable)"""
        if not output_file:
            output_file = f"{network_data['model_name']}.json"

        with open(output_file, 'w') as f:
            json.dump(network_data, f, indent=2)

        print(f"✅ Exported to {output_file} ({self._file_size(output_file)})")
        return output_file

    def _export_binary(self, network_data, output_file=None):
        """Export as compact binary (efficient storage)"""
        if not output_file:
            output_file = f"{network_data['model_name']}.bin"

        # Serialize to JSON then compress with gzip
        json_str = json.dumps(network_data)
        with gzip.open(output_file, 'wb') as f:
            f.write(json_str.encode('utf-8'))

        print(f"✅ Exported to {output_file} ({self._file_size(output_file)})")
        return output_file

    def _export_python(self, network_data, output_file=None):
        """Export as Python code (runnable without database)"""
        if not output_file:
            output_file = f"{network_data['model_name']}.py"

        # Generate Python code
        code = f'''#!/usr/bin/env python3
"""
Exported Neural Network: {network_data['model_name']}
Generated: {datetime.now().isoformat()}

This is a standalone Python file that contains the trained network.
No dependencies required - just Python stdlib!
"""

import json

# Network metadata
MODEL_NAME = "{network_data['model_name']}"
DESCRIPTION = "{network_data['description'] or ''}"
INPUT_SIZE = {network_data['input_size']}
HIDDEN_SIZES = {network_data['hidden_sizes']}
OUTPUT_SIZE = {network_data['output_size']}
TRAINED_AT = "{network_data['trained_at']}"

# Network weights and biases
MODEL_DATA = {json.dumps(network_data['model_data'], indent=2)}

def predict(input_data):
    """
    Make a prediction using this network

    Args:
        input_data: List of {INPUT_SIZE} numbers

    Returns:
        List of {OUTPUT_SIZE} numbers (prediction)
    """
    # Import neural network inference code
    from pure_neural_network import PureNeuralNetwork

    # Reconstruct network
    network = PureNeuralNetwork(INPUT_SIZE, HIDDEN_SIZES[0], OUTPUT_SIZE)
    network.input_weights = MODEL_DATA['weights'][0]
    network.output_weights = MODEL_DATA['weights'][1]
    network.hidden_biases = MODEL_DATA['biases'][0]
    network.output_biases = MODEL_DATA['biases'][1]

    # Predict
    return network.predict(input_data)

if __name__ == '__main__':
    print(f"Neural Network: {{MODEL_NAME}}")
    print(f"Description: {{DESCRIPTION}}")
    print(f"Architecture: {{INPUT_SIZE}} → {{HIDDEN_SIZES}} → {{OUTPUT_SIZE}}")
    print(f"Trained: {{TRAINED_AT}}")
    print()
    print("Test prediction:")
    print(predict([0.5] * INPUT_SIZE))
'''

        with open(output_file, 'w') as f:
            f.write(code)

        # Make executable
        os.chmod(output_file, 0o755)

        print(f"✅ Exported to {output_file} ({self._file_size(output_file)})")
        print(f"   Run: python3 {output_file}")
        return output_file

    def _export_numpy_compat(self, network_data, output_file=None):
        """Export in numpy-compatible format (for compatibility with other tools)"""
        if not output_file:
            output_file = f"{network_data['model_name']}_weights.npz.json"

        # Convert to numpy-like structure
        numpy_compat = {
            'metadata': {
                'model_name': network_data['model_name'],
                'description': network_data['description'],
                'architecture': {
                    'input_size': network_data['input_size'],
                    'hidden_sizes': network_data['hidden_sizes'],
                    'output_size': network_data['output_size']
                },
                'trained_at': network_data['trained_at']
            },
            'arrays': {
                'input_weights': network_data['model_data'].get('weights', [[]])[0],
                'output_weights': network_data['model_data'].get('weights', [[], []])[1],
                'hidden_biases': network_data['model_data'].get('biases', [[]])[0],
                'output_biases': network_data['model_data'].get('biases', [[], []])[1],
                'loss_history': network_data['model_data'].get('loss_history', []),
                'accuracy_history': network_data['model_data'].get('accuracy_history', [])
            }
        }

        with open(output_file, 'w') as f:
            json.dump(numpy_compat, f, indent=2)

        print(f"✅ Exported to {output_file} ({self._file_size(output_file)})")
        return output_file

    # ========================================================================
    # 2. IMPORT NETWORKS
    # ========================================================================

    def import_network(self, import_file, new_name=None, overwrite=False):
        """
        Import a neural network from a file

        Args:
            import_file: Path to exported network file
            new_name: Optional new name for imported network
            overwrite: If True, overwrite existing network with same name

        Returns:
            Imported network name
        """
        # Detect format from file extension
        if import_file.endswith('.json'):
            network_data = self._import_json(import_file)
        elif import_file.endswith('.bin'):
            network_data = self._import_binary(import_file)
        elif import_file.endswith('.tar.gz'):
            network_data = self._import_package(import_file)
        else:
            # Try JSON as default
            network_data = self._import_json(import_file)

        # Rename if requested
        if new_name:
            network_data['model_name'] = new_name

        # Insert into database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if exists
        cursor.execute('SELECT id FROM neural_networks WHERE model_name = ?',
                      (network_data['model_name'],))
        exists = cursor.fetchone()

        if exists and not overwrite:
            conn.close()
            raise ValueError(f"Network '{network_data['model_name']}' already exists. Use --overwrite to replace.")

        if exists:
            # Update
            cursor.execute('''
                UPDATE neural_networks
                SET description = ?, input_size = ?, hidden_sizes = ?,
                    output_size = ?, model_data = ?, trained_at = ?
                WHERE model_name = ?
            ''', (
                network_data['description'],
                network_data['input_size'],
                json.dumps(network_data['hidden_sizes']),
                network_data['output_size'],
                json.dumps(network_data['model_data']),
                network_data['trained_at'],
                network_data['model_name']
            ))
        else:
            # Insert
            cursor.execute('''
                INSERT INTO neural_networks
                (model_name, description, input_size, hidden_sizes, output_size, model_data, trained_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                network_data['model_name'],
                network_data['description'],
                network_data['input_size'],
                json.dumps(network_data['hidden_sizes']),
                network_data['output_size'],
                json.dumps(network_data['model_data']),
                network_data['trained_at']
            ))

        conn.commit()
        conn.close()

        print(f"✅ Imported '{network_data['model_name']}' successfully")
        return network_data['model_name']

    def _import_json(self, file_path):
        """Import from JSON file"""
        with open(file_path, 'r') as f:
            return json.load(f)

    def _import_binary(self, file_path):
        """Import from binary file"""
        with gzip.open(file_path, 'rb') as f:
            json_str = f.read().decode('utf-8')
            return json.loads(json_str)

    def _import_package(self, file_path):
        """Import from tarball package"""
        # Extract tarball to temp directory
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with tarfile.open(file_path, 'r:gz') as tar:
                tar.extractall(tmpdir)

            # Read network.json
            network_file = os.path.join(tmpdir, 'network.json')
            with open(network_file, 'r') as f:
                return json.load(f)

    # ========================================================================
    # 3. CREATE PACKAGES
    # ========================================================================

    def create_package(self, model_name, output_file=None, include_readme=True):
        """
        Create a shareable tarball package

        Args:
            model_name: Network to package
            output_file: Output filename (default: model_name.tar.gz)
            include_readme: Include README with usage instructions

        Returns:
            Path to created package
        """
        if not output_file:
            output_file = f"{model_name}.tar.gz"

        # Fetch network
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM neural_networks WHERE model_name = ?', (model_name,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError(f"Network '{model_name}' not found")

        network_data = {
            'id': row[0],
            'model_name': row[1],
            'description': row[2],
            'input_size': row[3],
            'hidden_sizes': json.loads(row[4]) if row[4] else [],
            'output_size': row[5],
            'model_data': json.loads(row[6]) if row[6] else {},
            'trained_at': row[7]
        }

        # Create package in temp directory
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write network.json
            network_file = os.path.join(tmpdir, 'network.json')
            with open(network_file, 'w') as f:
                json.dump(network_data, f, indent=2)

            # Write metadata.json
            metadata = {
                'package_name': model_name,
                'version': '1.0.0',
                'created_at': datetime.now().isoformat(),
                'architecture': f"{network_data['input_size']} → {network_data['hidden_sizes']} → {network_data['output_size']}",
                'accuracy': network_data['model_data'].get('accuracy_history', [])[-1] if network_data['model_data'].get('accuracy_history') else None,
                'total_epochs': len(network_data['model_data'].get('loss_history', [])),
                'export_format': 'soulfra-network-v1'
            }
            metadata_file = os.path.join(tmpdir, 'metadata.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            # Write README if requested
            if include_readme:
                readme_file = os.path.join(tmpdir, 'README.md')
                readme_content = f'''# {model_name}

{network_data['description'] or 'Neural network package'}

## Architecture

- **Input:** {network_data['input_size']} neurons
- **Hidden:** {network_data['hidden_sizes']} neurons
- **Output:** {network_data['output_size']} neurons
- **Trained:** {network_data['trained_at']}

## Performance

'''
                if network_data['model_data'].get('accuracy_history'):
                    final_accuracy = network_data['model_data']['accuracy_history'][-1]
                    readme_content += f"- **Accuracy:** {final_accuracy * 100:.2f}%\n"
                if network_data['model_data'].get('loss_history'):
                    final_loss = network_data['model_data']['loss_history'][-1]
                    readme_content += f"- **Loss:** {final_loss:.4f}\n"
                    readme_content += f"- **Epochs:** {len(network_data['model_data']['loss_history'])}\n"

                readme_content += f'''
## Usage

```python
# Import the network
from publish import NeuralNetworkPublisher

publisher = NeuralNetworkPublisher()
publisher.import_network('{output_file}')

# Use it
from neural_network import load_neural_network
network = load_neural_network('{model_name}')
prediction = network.predict(your_input)
```

## Package Contents

- `network.json` - Trained weights and biases
- `metadata.json` - Package metadata
- `README.md` - This file

---

Generated with Soulfra Neural Network Publisher
'''
                with open(readme_file, 'w') as f:
                    f.write(readme_content)

            # Create tarball
            with tarfile.open(output_file, 'w:gz') as tar:
                tar.add(network_file, arcname='network.json')
                tar.add(metadata_file, arcname='metadata.json')
                if include_readme:
                    tar.add(readme_file, arcname='README.md')

        print(f"✅ Created package: {output_file} ({self._file_size(output_file)})")
        print(f"   Share this file with others!")
        return output_file

    # ========================================================================
    # 4. DIFF NETWORKS
    # ========================================================================

    def diff_networks(self, model1_name, model2_name):
        """
        Show differences between two networks

        Args:
            model1_name: First network
            model2_name: Second network

        Returns:
            Dict of differences
        """
        # Fetch both networks
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM neural_networks WHERE model_name = ?', (model1_name,))
        row1 = cursor.fetchone()
        cursor.execute('SELECT * FROM neural_networks WHERE model_name = ?', (model2_name,))
        row2 = cursor.fetchone()
        conn.close()

        if not row1:
            raise ValueError(f"Network '{model1_name}' not found")
        if not row2:
            raise ValueError(f"Network '{model2_name}' not found")

        # Parse networks
        net1 = {
            'model_name': row1[1],
            'input_size': row1[3],
            'hidden_sizes': json.loads(row1[4]) if row1[4] else [],
            'output_size': row1[5],
            'model_data': json.loads(row1[6]) if row1[6] else {},
            'trained_at': row1[7]
        }
        net2 = {
            'model_name': row2[1],
            'input_size': row2[3],
            'hidden_sizes': json.loads(row2[4]) if row2[4] else [],
            'output_size': row2[5],
            'model_data': json.loads(row2[6]) if row2[6] else {},
            'trained_at': row2[7]
        }

        # Calculate differences
        diff = {
            'architecture_changed': (
                net1['input_size'] != net2['input_size'] or
                net1['hidden_sizes'] != net2['hidden_sizes'] or
                net1['output_size'] != net2['output_size']
            ),
            'accuracy_change': None,
            'loss_change': None,
            'weight_changes': 0,
            'training_time_diff': None
        }

        # Accuracy change
        if (net1['model_data'].get('accuracy_history') and
            net2['model_data'].get('accuracy_history')):
            acc1 = net1['model_data']['accuracy_history'][-1]
            acc2 = net2['model_data']['accuracy_history'][-1]
            diff['accuracy_change'] = acc2 - acc1

        # Loss change
        if (net1['model_data'].get('loss_history') and
            net2['model_data'].get('loss_history')):
            loss1 = net1['model_data']['loss_history'][-1]
            loss2 = net2['model_data']['loss_history'][-1]
            diff['loss_change'] = loss2 - loss1

        # Count weight changes
        if (net1['model_data'].get('weights') and
            net2['model_data'].get('weights')):
            weights1 = self._flatten_weights(net1['model_data']['weights'])
            weights2 = self._flatten_weights(net2['model_data']['weights'])
            if len(weights1) == len(weights2):
                diff['weight_changes'] = sum(1 for w1, w2 in zip(weights1, weights2) if abs(w1 - w2) > 0.0001)

        # Print diff
        print(f"\n=== Diff: {model1_name} → {model2_name} ===\n")
        print(f"Architecture changed: {'Yes' if diff['architecture_changed'] else 'No'}")
        if diff['accuracy_change'] is not None:
            sign = '+' if diff['accuracy_change'] >= 0 else ''
            print(f"Accuracy change: {sign}{diff['accuracy_change'] * 100:.2f}%")
        if diff['loss_change'] is not None:
            sign = '+' if diff['loss_change'] >= 0 else ''
            print(f"Loss change: {sign}{diff['loss_change']:.4f}")
        print(f"Weights changed: {diff['weight_changes']}")
        print(f"\nTraining dates:")
        print(f"  {model1_name}: {net1['trained_at']}")
        print(f"  {model2_name}: {net2['trained_at']}")
        print()

        return diff

    def _flatten_weights(self, weights):
        """Flatten nested weight arrays"""
        flat = []
        for layer in weights:
            for row in layer:
                if isinstance(row, list):
                    flat.extend(row)
                else:
                    flat.append(row)
        return flat

    # ========================================================================
    # 5. LIST NETWORKS
    # ========================================================================

    def list_networks(self, detailed=False):
        """
        List all available networks

        Args:
            detailed: Show detailed info

        Returns:
            List of network info dicts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM neural_networks ORDER BY trained_at DESC')
        rows = cursor.fetchall()
        conn.close()

        networks = []
        for row in rows:
            network_info = {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'architecture': f"{row[3]} → {row[4]} → {row[5]}",
                'trained_at': row[7]
            }

            if detailed:
                model_data = json.loads(row[6]) if row[6] else {}
                if model_data.get('accuracy_history'):
                    network_info['accuracy'] = model_data['accuracy_history'][-1]
                if model_data.get('loss_history'):
                    network_info['loss'] = model_data['loss_history'][-1]
                    network_info['epochs'] = len(model_data['loss_history'])

            networks.append(network_info)

        # Print table
        print(f"\n{'ID':<5} {'Name':<40} {'Architecture':<20} {'Trained':<20}")
        print("=" * 90)
        for net in networks:
            print(f"{net['id']:<5} {net['name']:<40} {net['architecture']:<20} {net['trained_at']:<20}")
            if detailed:
                if 'accuracy' in net:
                    print(f"      Accuracy: {net['accuracy'] * 100:.2f}% | Loss: {net.get('loss', 'N/A'):.4f} | Epochs: {net.get('epochs', 'N/A')}")
        print()

        return networks

    # ========================================================================
    # UTILITIES
    # ========================================================================

    def _file_size(self, file_path):
        """Get human-readable file size"""
        size = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# ==============================================================================
# CLI INTERFACE
# ==============================================================================

def main():
    """Command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Neural Network Publishing Toolkit - Git for AI'
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export a neural network')
    export_parser.add_argument('model_name', help='Name of the network to export')
    export_parser.add_argument('--format', choices=['json', 'binary', 'python', 'numpy_compat'],
                              default='json', help='Export format')
    export_parser.add_argument('--output', '-o', help='Output filename')

    # Import command
    import_parser = subparsers.add_parser('import', help='Import a neural network')
    import_parser.add_argument('file', help='File to import')
    import_parser.add_argument('--name', help='New name for imported network')
    import_parser.add_argument('--overwrite', action='store_true', help='Overwrite existing network')

    # Package command
    package_parser = subparsers.add_parser('package', help='Create a shareable package')
    package_parser.add_argument('model_name', help='Network to package')
    package_parser.add_argument('--output', '-o', help='Output filename')
    package_parser.add_argument('--no-readme', action='store_true', help='Don\'t include README')

    # Diff command
    diff_parser = subparsers.add_parser('diff', help='Show differences between networks')
    diff_parser.add_argument('model1', help='First network')
    diff_parser.add_argument('model2', help='Second network')

    # List command
    list_parser = subparsers.add_parser('list', help='List all networks')
    list_parser.add_argument('--detailed', '-d', action='store_true', help='Show detailed info')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    publisher = NeuralNetworkPublisher()

    try:
        if args.command == 'export':
            publisher.export_network(args.model_name, args.format, args.output)

        elif args.command == 'import':
            publisher.import_network(args.file, args.name, args.overwrite)

        elif args.command == 'package':
            publisher.create_package(args.model_name, args.output, not args.no_readme)

        elif args.command == 'diff':
            publisher.diff_networks(args.model1, args.model2)

        elif args.command == 'list':
            publisher.list_networks(args.detailed)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
