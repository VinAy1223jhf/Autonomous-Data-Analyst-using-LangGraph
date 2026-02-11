# tests/test_python_executor.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from tools.python_executor import run_plot_code


class TestRunPlotCode:
    """Test suite for the run_plot_code function."""
    
    @patch('tools.python_executor.plt')
    def test_executes_valid_bar_chart_code(self, mock_plt):
        """Should execute valid matplotlib bar chart code without errors."""
        # Arrange
        code = """
categories = ['Male', 'Female']
counts = [60, 40]
plt.bar(categories, counts)
plt.title('Sex Distribution')
plt.show()
"""
        data = [{"Sex": "Male"}, {"Sex": "Female"}]
        
        # Act
        run_plot_code(code, data)
        
        # Assert
        mock_plt.bar.assert_called_once()
        mock_plt.title.assert_called_once_with('Sex Distribution')
        mock_plt.show.assert_called_once()
    
    @patch('tools.python_executor.plt')
    def test_executes_valid_line_chart_code(self, mock_plt):
        """Should execute valid matplotlib line chart code."""
        # Arrange
        code = """
ages = [d['age'] for d in data]
plt.plot(ages)
plt.xlabel('Index')
plt.ylabel('Age')
plt.show()
"""
        data = [{"age": 25}, {"age": 30}, {"age": 35}]
        
        # Act
        run_plot_code(code, data)
        
        # Assert
        mock_plt.plot.assert_called_once()
        mock_plt.xlabel.assert_called_once_with('Index')
        mock_plt.ylabel.assert_called_once_with('Age')
        mock_plt.show.assert_called_once()
    
    @patch('tools.python_executor.plt')
    def test_data_variable_accessible_in_code(self, mock_plt):
        """Should make 'data' variable accessible within execution context."""
        # Arrange
        code = """
result = len(data)
plt.bar(['Count'], [result])
plt.show()
"""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        
        # Act
        run_plot_code(code, data)
        
        # Assert
        mock_plt.bar.assert_called_once_with(['Count'], [3])
    
    @patch('tools.python_executor.plt')
    def test_allows_safe_builtins(self, mock_plt):
        """Should allow safe built-in functions like len, range, sum."""
        # Arrange
        code = """
values = [1, 2, 3, 4, 5]
total = sum(values)
avg = total / len(values)
plt.bar(['Average'], [avg])
plt.show()
"""
        data = []
        
        # Act
        run_plot_code(code, data)
        
        # Assert
        mock_plt.bar.assert_called_once_with(['Average'], [3.0])
    
    @patch('tools.python_executor.plt')
    def test_raises_error_on_invalid_syntax(self, mock_plt):
        """Should raise RuntimeError when code has syntax errors."""
        # Arrange
        code = "plt.bar(['A'], [1]"  # Missing closing parenthesis
        data = []
        
        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            run_plot_code(code, data)
        
        assert "Plot execution failed" in str(exc_info.value)
    
    @patch('tools.python_executor.plt')
    def test_raises_error_on_undefined_variable(self, mock_plt):
        """Should raise RuntimeError when code references undefined variables."""
        # Arrange
        code = """
plt.bar(undefined_variable, [1, 2])
plt.show()
"""
        data = []
        
        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            run_plot_code(code, data)
        
        assert "Plot execution failed" in str(exc_info.value)
    
    @patch('tools.python_executor.plt')
    def test_blocks_unsafe_imports(self, mock_plt):
        """Should block import statements (not in safe_globals)."""
        # Arrange
        code = """
import os
plt.bar(['A'], [1])
plt.show()
"""
        data = []
        
        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            run_plot_code(code, data)
        
        assert "Plot execution failed" in str(exc_info.value)
    
    @patch('tools.python_executor.plt')
    def test_blocks_file_operations(self, mock_plt):
        """Should block file operations like open()."""
        # Arrange
        code = """
with open('/etc/passwd', 'r') as f:
    content = f.read()
plt.bar(['A'], [1])
plt.show()
"""
        data = []
        
        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            run_plot_code(code, data)
        
        assert "Plot execution failed" in str(exc_info.value)
    
    @patch('tools.python_executor.plt')
    def test_handles_list_of_tuples_data(self, mock_plt):
        """Should handle data as list of tuples."""
        # Arrange
        code = """
values = [row[1] for row in data]
plt.bar(['A', 'B'], values)
plt.show()
"""
        data = [("Male", 60), ("Female", 40)]
        
        # Act
        run_plot_code(code, data)
        
        # Assert
        mock_plt.bar.assert_called_once_with(['A', 'B'], [60, 40])
    
    @patch('tools.python_executor.plt')
    def test_handles_empty_data(self, mock_plt):
        """Should handle empty data gracefully."""
        # Arrange
        code = """
if len(data) == 0:
    plt.text(0.5, 0.5, 'No data')
else:
    plt.bar(['A'], [1])
plt.show()
"""
        data = []
        
        # Act
        run_plot_code(code, data)
        
        # Assert
        mock_plt.text.assert_called_once_with(0.5, 0.5, 'No data')
    
    @patch('tools.python_executor.plt')
    def test_allows_list_comprehensions(self, mock_plt):
        """Should allow list comprehensions and other safe Python constructs."""
        # Arrange
        code = """
sexes = [d['Sex'] for d in data]
male_count = sum(1 for s in sexes if s == 'Male')
female_count = sum(1 for s in sexes if s == 'Female')
plt.bar(['Male', 'Female'], [male_count, female_count])
plt.show()
"""
        data = [
            {"Sex": "Male"},
            {"Sex": "Female"},
            {"Sex": "Male"},
            {"Sex": "Male"}
        ]
        
        # Act
        run_plot_code(code, data)
        
        # Assert
        mock_plt.bar.assert_called_once_with(['Male', 'Female'], [3, 1])
    
    @patch('tools.python_executor.plt')
    def test_traceback_printed_on_error(self, mock_plt, capsys):
        """Should print traceback when execution fails."""
        # Arrange
        code = "raise ValueError('Test error')"
        data = []
        
        # Act & Assert
        with pytest.raises(RuntimeError):
            run_plot_code(code, data)
        
        # Check that traceback was printed
        captured = capsys.readouterr()
        assert "Traceback" in captured.err or "ValueError" in str(captured)


class TestRunPlotCodeEdgeCases:
    """Edge case tests for run_plot_code."""
    
    @patch('tools.python_executor.plt')
    def test_handles_unicode_in_data(self, mock_plt):
        """Should handle Unicode characters in data."""
        # Arrange
        code = """
names = [d['name'] for d in data]
plt.bar(names, [1, 1])
plt.show()
"""
        data = [{"name": "José"}, {"name": "François"}]
        
        # Act
        run_plot_code(code, data)
        
        # Assert
        mock_plt.bar.assert_called_once()
    
    @patch('tools.python_executor.plt')
    def test_handles_complex_matplotlib_calls(self, mock_plt):
        """Should handle multiple matplotlib operations."""
        # Arrange
        code = """
fig, (ax1, ax2) = plt.subplots(1, 2)
ax1.bar(['A'], [1])
ax2.plot([1, 2, 3])
plt.tight_layout()
plt.show()
"""
        data = []
        
        # Act
        run_plot_code(code, data)
        
        # Assert
        mock_plt.subplots.assert_called_once()
        mock_plt.tight_layout.assert_called_once()
        mock_plt.show.assert_called_once()
    
    @patch('tools.python_executor.plt')
    def test_code_with_comments(self, mock_plt):
        """Should handle code with comments."""
        # Arrange
        code = """
# Extract data
values = [d['value'] for d in data]
# Create plot
plt.bar(['A', 'B'], values)
# Display
plt.show()
"""
        data = [{"value": 10}, {"value": 20}]
        
        # Act
        run_plot_code(code, data)
        
        # Assert
        mock_plt.bar.assert_called_once_with(['A', 'B'], [10, 20])