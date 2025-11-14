import unittest
import numpy as np
from unittest.mock import patch, MagicMock
from plans.utils import get_model, compute_sqft, polygon_dimension
import plans.utils as model_utils

class UtilsTestCase(unittest.TestCase):
    def setUp(self):
        # Clear singleton cache before each test
        model_utils._model_instance = None

    @patch("plans.utils.YOLO")
    def test_get_model_singleton(self, mock_yolo):
        # Setup
        mock_model = MagicMock()
        mock_yolo.return_value = mock_model

        # Act
        model1 = get_model()
        model2 = get_model()

        # Assert
        self.assertIs(model1, model2)
        mock_yolo.assert_called_once()  # Ensures YOLO is only initialized once

    def test_compute_sqft_correct_area(self):
        points = np.array([[0, 0], [0, 10], [10, 10], [10, 0]])
        dpi = 100
        scale = 1
        expected_area = (10 / dpi / scale) ** 2
        actual_area = compute_sqft(points, dpi, scale)
        self.assertAlmostEqual(actual_area, expected_area, places=4)

    def test_polygon_dimension_correct_output(self):
        points = np.array([[0, 0], [0, 10], [20, 10], [20, 0]])
        dpi = 100
        scale = 1
        width_expected = 20 / dpi / scale
        height_expected = 10 / dpi / scale
        width, height = polygon_dimension(points, dpi, scale)
        self.assertAlmostEqual(width, width_expected, places=2)
        self.assertAlmostEqual(height, height_expected, places=2)

# if __name__ == '__main__':
#     unittest.main()
