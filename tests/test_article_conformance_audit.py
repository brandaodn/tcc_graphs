"""Static article-conformance audit: documents known differences.
Run: python -m unittest discover -s tests -p 'test_article_conformance_audit.py' -v
Does NOT certify correctness of the original code or the experimental variant.
"""
import ast
import inspect
import unittest
from graphs import duan_et_al


class ArticleConformanceAudit(unittest.TestCase):
    def test_legacy_quota_differs_from_algorithm_three(self):
        tree = ast.parse(inspect.getsource(duan_et_al.BMSSP))
        conditions = [node.test for node in ast.walk(tree) if isinstance(node, ast.While)]
        self.assertEqual(len(conditions), 1)
        quota = ast.unparse(conditions[0])
        # Explicitly RECORD current deviation, not an endorsement.
        self.assertIn('k ** 2', quota)

    def test_legacy_frontier_depends_on_improvement(self):
        tree = ast.parse(inspect.getsource(duan_et_al.BMSSP))
        self.assertTrue(any(
            isinstance(node, ast.If) and isinstance(node.test, ast.Name)
            and node.test.id == 'accepted'
            for node in ast.walk(tree)
        ))

    def test_legacy_does_not_transform_constant_degree(self):
        source = inspect.getsource(duan_et_al.sssp_duan_et_al)
        self.assertNotIn('constant_degree', source)


if __name__ == '__main__':
    unittest.main()
