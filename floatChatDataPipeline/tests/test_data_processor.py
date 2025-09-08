import pytest
import numpy as np
import pandas as pd
import xarray as xr
from unittest.mock import MagicMock, patch
from src.data_processor import DataProcessor

# --- Test Fixtures ---

@pytest.fixture
def mock_dependencies():
    def mock_encode_side_effect(sentences, **kwargs):  # accept **kwargs
        return [[0.1] * 384 for _ in sentences]  # fake embedding vectors

    mock_embedding_model = MagicMock()
    mock_embedding_model.encode.side_effect = mock_encode_side_effect

    return {
        "embedding_model": mock_embedding_model,
        "faiss_index": MagicMock(),
        "chroma_collection": MagicMock(),
        "pg_session": MagicMock(),
    }

@pytest.fixture
def dummy_nc_file(tmp_path):
    """Creates a temporary, valid NetCDF file for testing."""
    file_path = tmp_path / "test_data.nc"
    
    data = xr.Dataset(
        {
            "PSAL": (("time", "depth", "latitude", "longitude"), np.random.rand(1, 2, 2, 2)),
            "TEMP": (("time", "depth", "latitude", "longitude"), np.random.rand(1, 2, 2, 2)),
        },
        coords={
            "time": pd.to_datetime(["2025-01-01"]),
            "depth": [10, 20],
            "latitude": [45.0, 46.0],
            "longitude": [-120.0, -121.0],
        },
        attrs={"platform_id": "TEST_FLOAT_123"}
    )
    data["PSAL"][0, 0, 0, 0] = np.nan
    
    data.to_netcdf(file_path)
    return file_path

# --- Unit Tests ---

def test_extract_data_from_nc(dummy_nc_file, mock_dependencies):
    """Tests that the data extraction correctly reads and cleans the NetCDF file."""
    processor = DataProcessor(**mock_dependencies)
    df = processor._extract_data_from_nc(dummy_nc_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 7
    assert 'PSAL' in df.columns
    assert 'TEMP' in df.columns
    assert 'float_wmo_id' in df.columns
    assert df['float_wmo_id'].iloc[0] == "TEST_FLOAT_123"

def test_generate_summary(mock_dependencies):
    """Tests the text summary generation logic."""
    processor = DataProcessor(**mock_dependencies)
    sample_row = pd.Series({
        "time": pd.Timestamp("2025-09-08"),
        "latitude": 45.5,
        "longitude": -122.3,
        "float_wmo_id": "TEST1",
        "PSAL": 35.123,
        "TEMP": 15.456
    })
    
    summary = processor._generate_summary(sample_row)
    
    # Fixed assertions to match the actual output format
    assert "Data point from 2025-09-08 float TEST1" in summary
    assert "at location (45.50, -122.30)" in summary
    assert "Practical salinity was 35.12 PSS-78" in summary
    assert "Sea temperature was 15.46 degrees Celsius" in summary

@patch('src.data_processor.db_utils')
def test_process_file_integration(mock_db_utils, dummy_nc_file, mock_dependencies):
    """
    Tests the main process_file method to ensure it calls all sub-components correctly.
    """
    mock_db_utils.insert_profiles_batch.return_value = list(range(7))
    processor = DataProcessor(**mock_dependencies)
    processor.process_file(dummy_nc_file)
    
    mock_db_utils.insert_profiles_batch.assert_called_once()
    assert len(mock_db_utils.insert_profiles_batch.call_args[0][1]) == 7

    mock_dependencies["chroma_collection"].add.assert_called_once()
    mock_dependencies["faiss_index"].add_with_ids.assert_called_once()
    
    assert len(mock_dependencies["chroma_collection"].add.call_args.kwargs['embeddings']) == 7
    assert mock_dependencies["faiss_index"].add_with_ids.call_args[0][0].shape[0] == 7