# tests/test_viz_agent_e2e.py
"""
End-to-End Integration Tests for Visualization Agent

This file tests the COMPLETE FLOW:
User Query → Viz Agent → SQL Agent → Code Generation → Python Executor → Plot

Run with: pytest tests/test_viz_agent_e2e.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from agents.viz_agent import generate_viz_code, strip_code_markers, sanitize_plot_code
from tools.python_executor import run_plot_code


class TestEndToEndVisualizationFlow:
    """
    Complete end-to-end tests simulating real user queries.
    These tests mock the SQL agent but use the actual viz agent and executor.
    """
    
    @patch('tools.python_executor.plt')
    @patch('agents.viz_agent.llm')
    def test_pie_chart_for_gender_distribution(self, mock_llm, mock_plt):
        """
        USER QUERY: "Generate pie chart for female and male percentages"
        
        Flow:
        1. SQL Agent returns gender counts (mocked)
        2. Viz Agent generates matplotlib pie chart code
        3. Python Executor runs the code
        4. Plot is created
        """
        # ============================================
        # STEP 1: Simulate SQL Agent Response
        # ============================================
        sql_result = [
            {"Sex": "Male", "count": 52},
            {"Sex": "Female", "count": 48}
        ]
        
        # Transform data for visualization (this would be done by supervisor/viz agent)
        transformed_data = {
            'categories': ['Male', 'Female'],
            'counts': [52, 48],
            'total': 100
        }
        
        # ============================================
        # STEP 2: Mock LLM to Generate Pie Chart Code
        # ============================================
        user_query = "Generate pie chart for female and male percentages"
        
        # Simulate LLM generating matplotlib code (with backticks)
        mock_response = Mock()
        mock_response.content = """```python
plt.pie(data['counts'], labels=data['categories'], autopct='%1.1f%%')
plt.title('Gender Distribution')
plt.show()
```"""
        mock_llm.invoke.return_value = mock_response
        
        # ============================================
        # STEP 3: Call Viz Agent (generates code)
        # ============================================
        plot_code = generate_viz_code(
            query=user_query,
            data=transformed_data,
            data_description=str(transformed_data)
        )
        
        # Verify backticks were stripped
        assert "```" not in plot_code
        assert "plt.pie" in plot_code
        assert "data['counts']" in plot_code
        assert "data['categories']" in plot_code
        
        # ============================================
        # STEP 4: Execute the Code with Python Executor
        # ============================================
        run_plot_code(plot_code, transformed_data)
        
        # ============================================
        # STEP 5: Verify Plot Was Created
        # ============================================
        # Check that plt.pie was called with correct data
        mock_plt.pie.assert_called_once()
        call_args = mock_plt.pie.call_args
        
        # Verify the data passed to pie chart
        assert list(call_args[0][0]) == [52, 48]  # counts
        
        # Verify plt.show() was called
        mock_plt.show.assert_called_once()
        
        print("\n✅ END-TO-END TEST PASSED: Pie chart generated successfully!")
    
    @patch('tools.python_executor.plt')
    @patch('agents.viz_agent.llm')
    def test_bar_chart_for_job_title_distribution(self, mock_llm, mock_plt):
        """
        USER QUERY: "Create bar chart showing top 5 job titles"
        
        Flow:
        1. SQL Agent returns job title counts
        2. Viz Agent generates bar chart code
        3. Python Executor runs it
        4. Bar chart is displayed
        """
        # ============================================
        # STEP 1: Simulate SQL Agent Response
        # ============================================
        sql_result = [
            {"Job Title": "Engineer", "count": 15},
            {"Job Title": "Manager", "count": 12},
            {"Job Title": "Analyst", "count": 10},
            {"Job Title": "Designer", "count": 8},
            {"Job Title": "Developer", "count": 7}
        ]
        
        # Transform for visualization
        transformed_data = {
            'categories': ['Engineer', 'Manager', 'Analyst', 'Designer', 'Developer'],
            'counts': [15, 12, 10, 8, 7],
            'total': 52
        }
        
        # ============================================
        # STEP 2: Mock LLM Response
        # ============================================
        user_query = "Create bar chart showing top 5 job titles"
        
        mock_response = Mock()
        mock_response.content = """plt.bar(data['categories'], data['counts'])
plt.xlabel('Job Title')
plt.ylabel('Count')
plt.title('Top 5 Job Titles')
plt.xticks(rotation=45)
plt.show()"""
        mock_llm.invoke.return_value = mock_response
        
        # ============================================
        # STEP 3: Generate Code
        # ============================================
        plot_code = generate_viz_code(
            query=user_query,
            data=transformed_data
        )
        
        assert "plt.bar" in plot_code
        assert "data['categories']" in plot_code or "data['counts']" in plot_code
        
        # ============================================
        # STEP 4: Execute Code
        # ============================================
        run_plot_code(plot_code, transformed_data)
        
        # ============================================
        # STEP 5: Verify
        # ============================================
        mock_plt.bar.assert_called_once()
        mock_plt.show.assert_called_once()
        
        print("\n✅ END-TO-END TEST PASSED: Bar chart generated successfully!")
    
    @patch('tools.python_executor.plt')
    @patch('agents.viz_agent.llm')
    def test_complete_workflow_with_code_sanitization(self, mock_llm, mock_plt):
        """
        Tests the COMPLETE workflow including code sanitization.
        
        Scenario: LLM generates code with import statements (which should be removed)
        """
        # ============================================
        # STEP 1: Data from SQL Agent
        # ============================================
        transformed_data = {
            'categories': ['Male', 'Female'],
            'counts': [60, 40],
            'total': 100
        }
        
        # ============================================
        # STEP 2: LLM Generates Code with Imports (BAD!)
        # ============================================
        user_query = "Show gender distribution as pie chart"
        
        mock_response = Mock()
        # LLM incorrectly includes import statement
        mock_response.content = """```python
import matplotlib.pyplot as plt

plt.pie(data['counts'], labels=data['categories'], autopct='%1.1f%%')
plt.title('Gender Distribution')
plt.show()
```"""
        mock_llm.invoke.return_value = mock_response
        
        # ============================================
        # STEP 3: Generate and Sanitize Code
        # ============================================
        plot_code = generate_viz_code(
            query=user_query,
            data=transformed_data
        )
        
        # Verify backticks removed
        assert "```" not in plot_code
        
        # Sanitize imports
        clean_code = sanitize_plot_code(plot_code)
        
        # Verify import was removed
        assert "import matplotlib" not in clean_code
        assert "import " not in clean_code
        
        # But plotting code should remain
        assert "plt.pie" in clean_code
        assert "plt.show()" in clean_code
        
        # ============================================
        # STEP 4: Execute Sanitized Code
        # ============================================
        run_plot_code(clean_code, transformed_data)
        
        # ============================================
        # STEP 5: Verify Success
        # ============================================
        mock_plt.pie.assert_called_once()
        mock_plt.show.assert_called_once()
        
        print("\n✅ END-TO-END TEST PASSED: Code sanitization working!")


class TestVisualizationWithRealDataFormat:
    """
    Tests using data in the EXACT format returned by SQL agent.
    This ensures compatibility between SQL agent and Viz agent.
    """
    
    @patch('tools.python_executor.plt')
    @patch('agents.viz_agent.llm')
    def test_handles_sql_agent_data_format(self, mock_llm, mock_plt):
        """
        Test with data in the exact format SQL agent returns.
        
        SQL Agent returns: [{"Sex": "Male"}, {"Sex": "Female"}, ...]
        This needs to be transformed before visualization.
        """
        # ============================================
        # Raw SQL Result (as returned by SQL agent)
        # ============================================
        raw_sql_result = [
            {"Sex": "Male"},
            {"Sex": "Male"},
            {"Sex": "Female"},
            {"Sex": "Male"},
            {"Sex": "Female"}
        ]
        
        # ============================================
        # Transform Data (done by supervisor or viz agent)
        # ============================================
        # Count occurrences
        from collections import Counter
        sex_counts = Counter(row["Sex"] for row in raw_sql_result)
        
        transformed_data = {
            'categories': list(sex_counts.keys()),
            'counts': list(sex_counts.values()),
            'total': len(raw_sql_result)
        }
        
        # ============================================
        # Mock LLM
        # ============================================
        mock_response = Mock()
        mock_response.content = """plt.pie(data['counts'], labels=data['categories'], autopct='%1.1f%%')
plt.title('Sex Distribution')
plt.show()"""
        mock_llm.invoke.return_value = mock_response
        
        # ============================================
        # Generate and Execute
        # ============================================
        plot_code = generate_viz_code(
            query="Plot sex distribution",
            data=transformed_data
        )
        
        run_plot_code(plot_code, transformed_data)
        
        # ============================================
        # Verify
        # ============================================
        mock_plt.pie.assert_called_once()
        assert mock_plt.pie.call_args[0][0] == list(sex_counts.values())
        
        print("\n✅ TEST PASSED: SQL agent data format handled correctly!")


class TestErrorHandling:
    """Tests error handling in the visualization pipeline."""
    
    @patch('agents.viz_agent.llm')
    def test_handles_llm_json_error(self, mock_llm):
        """Should handle cases where LLM returns invalid code."""
        # Mock LLM returning invalid code
        mock_response = Mock()
        mock_response.content = "This is not valid Python code!"
        mock_llm.invoke.return_value = mock_response
        
        # Generate code
        plot_code = generate_viz_code(
            query="Make a chart",
            data={'categories': ['A'], 'counts': [1]}
        )
        
        # Code should be returned even if invalid (executor will catch it)
        assert len(plot_code) > 0
        assert plot_code == "This is not valid Python code!"
    
    @patch('tools.python_executor.plt')
    def test_executor_raises_error_on_invalid_code(self, mock_plt):
        """Python executor should raise RuntimeError on invalid code."""
        invalid_code = "this is not valid python syntax!@#$"
        data = {'categories': ['A'], 'counts': [1]}
        
        with pytest.raises(RuntimeError) as exc_info:
            run_plot_code(invalid_code, data)
        
        assert "Plot execution failed" in str(exc_info.value)


class TestHelperFunctions:
    """Tests for utility functions."""
    
    def test_sanitize_plot_code_removes_imports(self):
        """Should remove all import statements."""
        code_with_imports = """import matplotlib.pyplot as plt
from numpy import array
import pandas as pd

plt.bar([1, 2], [3, 4])
plt.show()"""
        
        cleaned = sanitize_plot_code(code_with_imports)
        
        assert "import matplotlib" not in cleaned
        assert "from numpy" not in cleaned
        assert "import pandas" not in cleaned
        assert "plt.bar" in cleaned
        assert "plt.show()" in cleaned
    
    def test_sanitize_plot_code_preserves_valid_code(self):
        """Should preserve valid plotting code."""
        valid_code = """plt.pie([1, 2], labels=['A', 'B'])
plt.title('Test')
plt.show()"""
        
        cleaned = sanitize_plot_code(valid_code)
        
        assert cleaned == valid_code
    
    def test_strip_code_markers_comprehensive(self):
        """Comprehensive test for backtick stripping."""
        test_cases = [
            ("```python\ncode\n```", "code"),
            ("```\ncode\n```", "code"),
            ("`code`", "code"),
            ("code", "code"),
            ("", ""),
        ]
        
        for input_code, expected in test_cases:
            result = strip_code_markers(input_code)
            assert result == expected, f"Failed for input: {input_code}"


# ============================================
# MAIN TEST RUNNER
# ============================================

if __name__ == "__main__":
    """
    Run this file directly for a quick test:
    python tests/test_viz_agent_e2e.py
    """
    print("\n" + "="*60)
    print("RUNNING END-TO-END VISUALIZATION TESTS")
    print("="*60 + "\n")
    
    # Run pytest programmatically
    pytest.main([__file__, "-v", "--tb=short"])