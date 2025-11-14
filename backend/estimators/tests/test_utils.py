from django.test import TestCase
from unittest.mock import patch, MagicMock
from estimators import utils

class UtilsModelLoadTest(TestCase):
    def setUp(self):
        utils._wall_model_instance = None
        utils._window_and_door_model_instance = None

    @patch('estimators.utils.YOLO')
    @patch('estimators.utils.os.path.join')
    def test_get_wall_model_singleton(self, mock_join, mock_yolo):
        mock_join.return_value = 'fake/path/wall.pt'
        fake_model = MagicMock()
        fake_model.task = 'detect'
        mock_yolo.return_value = fake_model

        model1 = utils.get_wall_model()
        model2 = utils.get_wall_model()

        self.assertEqual(model1, model2)
        self.assertEqual(model1.task, 'detect')
        mock_yolo.assert_called_once_with('fake/path/wall.pt')

    @patch('estimators.utils.YOLO')
    @patch('estimators.utils.os.path.join')
    def test_get_window_and_door_model_singleton(self, mock_join, mock_yolo):
        mock_join.return_value = 'fake/path/window_door.pt'
        fake_model = MagicMock()
        fake_model.task = 'detect'
        mock_yolo.return_value = fake_model

        model1 = utils.get_window_and_door_model()
        model2 = utils.get_window_and_door_model()

        self.assertEqual(model1, model2)
        self.assertEqual(model1.task, 'detect')
        mock_yolo.assert_called_once_with('fake/path/window_door.pt')
