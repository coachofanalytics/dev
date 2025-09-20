"""
Documentation Optimizer Script
Consolidates and optimizes documentation files
"""
import os
import gzip
import logging
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentationOptimizer:
    """Documentation optimization utility class."""
    
    def __init__(self):
        """Initialize the optimizer with statistics tracking."""
        self.optimization_stats = {
            'files_processed': 0,
            'files_compressed': 0,
            'space_saved': 0,
            'errors': []
        }
        
        # Documentation directories to analyze
        self.docs_dirs = ['docs/', 'app/docs/']
    
    def find_large_documentation_files(self):
        """Find documentation files larger than 50KB."""
        large_files = []
        
        logger.info("Scanning for large documentation files...")
        
        for docs_dir in self.docs_dirs:
            if os.path.exists(docs_dir):
                for root, dirs, files in os.walk(docs_dir):
                    for file in files:
                        if file.endswith('.md'):
                            file_path = os.path.join(root, file)
                            file_size = os.path.getsize(file_path)
                            
                            if file_size > 50 * 1024:  # 50KB
                                large_files.append((file_path, file_size))
        
        logger.info(f"Found {len(large_files)} large documentation files")
        return large_files
    
    def compress_file(self, file_path):
        """Compress a single documentation file."""
        try:
            # Read original file
            with open(file_path, 'rb') as f_in:
                original_content = f_in.read()
            
            # Compress content
            compressed_content = gzip.compress(original_content)
            
            # Write compressed content back to file
            with open(file_path, 'wb') as f_out:
                f_out.write(compressed_content)
            
            # Update stats
            original_size = len(original_content)
            compressed_size = len(compressed_content)
            savings = original_size - compressed_size
            
            self.optimization_stats['files_processed'] += 1
            self.optimization_stats['files_compressed'] += 1
            self.optimization_stats['space_saved'] += savings
            
            logger.info(f"Compressed {file_path}: {original_size} → {compressed_size} bytes")
            
        except Exception as e:
            error_msg = f"Failed to compress {file_path}: {e}"
            logger.error(error_msg)
            self.optimization_stats['errors'].append(error_msg)
    
    def optimize_documentation(self):
        """Optimize all documentation files."""
        logger.info("Starting documentation optimization...")
        
        # Find large files
        large_files = self.find_large_documentation_files()
        
        # Compress large files
        for file_path, file_size in large_files:
            self.compress_file(file_path)
        
        # Optimize other documentation files
        self.optimize_all_documentation()
        
        logger.info("Documentation optimization completed!")
    
    def optimize_all_documentation(self):
        """Optimize all documentation files in the project."""
        for docs_dir in self.docs_dirs:
            if os.path.exists(docs_dir):
                self.optimize_directory(docs_dir)
    
    def optimize_directory(self, directory):
        """Optimize all documentation files in a directory."""
        if not os.path.exists(directory):
            return
            
        logger.info(f"Optimizing documentation in {directory}")
        
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.endswith('.md'):
                    file_path = os.path.join(root, filename)
                    
                    # Skip if already processed
                    if file_path in [f[0] for f in self.find_large_documentation_files()]:
                        continue
                    
                    # Get original size
                    original_size = os.path.getsize(file_path)
                    
                    # Only compress if file is larger than 10KB
                    if original_size > 10 * 1024:
                        self.compress_file(file_path)
    
    def consolidate_documentation(self):
        """Consolidate documentation by removing redundant content."""
        logger.info("Starting documentation consolidation...")
        
        # Find similar files
        similar_files = self.find_similar_documentation()
        
        # Consolidate similar files
        for file_group in similar_files:
            self.consolidate_file_group(file_group)
        
        logger.info("Documentation consolidation completed!")
    
    def find_similar_documentation(self):
        """Find documentation files with similar content."""
        # This is a simplified implementation
        # In a real scenario, you might use more sophisticated similarity detection
        similar_files = []
        
        for docs_dir in self.docs_dirs:
            if os.path.exists(docs_dir):
                for root, dirs, files in os.walk(docs_dir):
                    for file in files:
                        if file.endswith('.md'):
                            file_path = os.path.join(root, file)
                            
                            # Check for files with similar names
                            base_name = os.path.splitext(file)[0]
                            similar_files.append([file_path])
        
        return similar_files
    
    def consolidate_file_group(self, file_group):
        """Consolidate a group of similar files."""
        if len(file_group) <= 1:
            return
        
        # Keep the first file, remove the rest
        keep_file = file_group[0]
        
        for file_path in file_group[1:]:
            try:
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                self.optimization_stats['space_saved'] += file_size
                
                logger.info(f"Consolidated duplicate: {file_path}")
                
            except Exception as e:
                error_msg = f"Failed to consolidate {file_path}: {e}"
                logger.error(error_msg)
                self.optimization_stats['errors'].append(error_msg)
    
    def get_optimization_report(self):
        """Get optimization statistics."""
        return {
            'files_processed': self.optimization_stats['files_processed'],
            'files_compressed': self.optimization_stats['files_compressed'],
            'space_saved': self.optimization_stats['space_saved'],
            'errors': self.optimization_stats['errors']
        }
    
    def print_optimization_report(self):
        """Print a formatted optimization report."""
        report = self.get_optimization_report()
        
        print("\n" + "="*60)
        print("DOCUMENTATION OPTIMIZATION REPORT")
        print("="*60)
        print(f"Files processed: {report['files_processed']}")
        print(f"Files compressed: {report['files_compressed']}")
        print(f"Total space saved: {report['space_saved']:,} bytes ({report['space_saved']/1024:.2f} KB)")
        
        if report['errors']:
            print(f"\nErrors encountered: {len(report['errors'])}")
            for error in report['errors']:
                print(f"  - {error}")
        
        print("="*60)

def main():
    """Main function to run documentation optimization."""
    # Create optimizer instance
    optimizer = DocumentationOptimizer()
    
    # Run optimization
    optimizer.optimize_documentation()
    
    # Print report
    optimizer.print_optimization_report()

if __name__ == '__main__':
    main()

