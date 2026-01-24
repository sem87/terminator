from tiker_figi_json import *
from utils import *
import pytest
from unittest.mock import patch, MagicMock


class TestTikerFigiJson:
    @pytest.fixture()
    def data_share(self):
        """Фикстура с тестовыми данными акций"""
        return [{"name": "Сбербанк",
                 "figi": "BBG004730N88",
                 "ticker": "SBER",
                 "class_code": "TQBR"},
                {"name": "Газпром",
                 "figi": "BBG004730RP0",
                 "ticker": "GAZP",
                 "class_code": "TQBR"},
                {"name": "Яндекс",
                 "figi": "BBG006L8G4H1",
                 "ticker": "YNDX",
                 "class_code": "TQBR"}]

    @pytest.fixture
    def mock_cl(self, data_share):
        """Фикстура: мок-клиент Tinkoff, который возвращает data_share при запросе акций."""
        shares_mock = MagicMock()
        cl_mock = MagicMock()
        shares_mock.instruments = data_share
        cl_mock.instruments.shares.return_value = shares_mock
        return cl_mock

    @pytest.mark.parametrize("tiker,result",
                             [("SBER", "BBG004730N88"),
                              ("GAZP", "BBG004730RP0"),
                              ("YNDX", "BBG006L8G4H1"),
                              ("djdj", None)])
    def test_get_figi(self, mock_cl, tiker, result):
        assert get_figi(tiker=tiker, cl=mock_cl) == result

    def test_save_all_json(self):
        """ПРОТЕСТИТЬ НА СОХРАНЕНИЕ"""
        pass

    # def test_get_figi(self, data_share):
    #     # Настраиваем возврат shares()
    #     shares_mock = MagicMock()
    #     # Создаём мок-клиент cl, у которого cl.instruments == instruments_mock
    #     cl_mock = MagicMock()
    #     # Строим зависимости
    #     shares_mock.instruments = data_share  # ваши тестовые данные
    #     cl_mock.instruments.shares.return_value = shares_mock
    #     #  Вызываем функцию с мок-клиентом
    #     result = get_figi(tiker="GAZP", cl=cl_mock)
    #     #  Проверяем результат
    #     assert result == "BBG004730RP0"


class TestJsonutils:
    @pytest.fixture()
    def test_data(self):
        """Фикстура с тестовыми данными акций"""
        return {"SBER": "BBG004730N88", "GAZP": "BBG004730RP0", "YNDX": "BBG006L8G4H1"}

    @pytest.fixture()
    def test_get_json(self, test_data, tmp_path, monkeypatch):
        # Создаём временный JSON-файл
        json_file = tmp_path / "tiker_figi.json"
        json_file.write_text(json.dumps(test_data), encoding="utf-8")
        # Подменяем путь к файлу (или просто меняем рабочую директорию)
        monkeypatch.chdir(tmp_path)
        return json_file

    def test_read_tiker_figi_json_valid_file(self, test_data, test_get_json):
        assert read_tiker_figi_json() == test_data

    def test_read_tiker_figi_json_invalid_json(self, test_get_json, tmp_path, monkeypatch):
        json_file = tmp_path / "tiker_figi.json"
        json_file.write_text("{ неправильный json }", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        result = read_tiker_figi_json()
        assert result == {}

    def test_read_tiker_figi_json_file_not_found(self, monkeypatch, tmp_path):
        # Убеждаемся, что файла нет
        monkeypatch.chdir(tmp_path)  # в пустой папке
        result = read_tiker_figi_json()
        assert result == {}

    def test_read_tiker_figi_json_os_error(self, monkeypatch):
        # Имитируем OSError при открытии файла
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            result = read_tiker_figi_json()
            assert result == {}

    def test_read_tiker_figi_json_unexpected_exception(self, monkeypatch):
        # Имитируем неожиданное исключение
        with patch("builtins.open", side_effect=Exception("Что-то пошло не так")):
            with patch("json.load", side_effect=Exception("Unexpected")):
                result = read_tiker_figi_json()
                assert result == {}


class TestDataAnalysis:
    ...