import pytest
import requests
from unittest.mock import MagicMock, patch, mock_open
import sys
import os

# Import the module to test
# Since it's in the parent directory, we might need to adjust path if running from tests/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import deploy_fetch

def test_get_api_url():
    url = deploy_fetch.get_api_url('/some/path')
    assert url == 'https://www.pythonanywhere.com/api/v0/user/kobazauros/files/path/some/path'

def test_upload_file_success(mocker):
    # Mock os.path.exists to return True
    mocker.patch('os.path.exists', return_value=True)
    
    # Mock session.post
    mock_post = mocker.patch.object(deploy_fetch.session, 'post')
    mock_post.return_value.status_code = 200
    
    # Mock open
    m = mock_open(read_data=b"data")
    with patch('builtins.open', m):
        deploy_fetch.upload_file('local.txt', 'remote.txt')
        
    mock_post.assert_called_once()
    assert 'content' in mock_post.call_args[1]['files']

def test_upload_file_not_found(mocker, capsys):
    mocker.patch('os.path.exists', return_value=False)
    deploy_fetch.upload_file('missing.txt', 'remote.txt')
    captured = capsys.readouterr()
    assert "Skipped (Not found)" in captured.out

def test_upload_file_failure(mocker, capsys):
    mocker.patch('os.path.exists', return_value=True)
    mock_post = mocker.patch.object(deploy_fetch.session, 'post')
    mock_post.return_value.status_code = 500
    
    m = mock_open(read_data=b"data")
    with patch('builtins.open', m):
        deploy_fetch.upload_file('local.txt', 'remote.txt')
        
    captured = capsys.readouterr()
    assert "Failed (500)" in captured.out

def test_download_file_success(mocker):
    mock_get = mocker.patch.object(deploy_fetch.session, 'get')
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = b"content"
    
    m = mock_open()
    with patch('builtins.open', m):
        deploy_fetch.download_file('remote.txt', 'local.txt')
        
    m().write.assert_called_once_with(b"content")

def test_list_remote_files(mocker):
    mock_get = mocker.patch.object(deploy_fetch.session, 'get')
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"file.txt": {}}
    
    result = deploy_fetch.list_remote_files('/dir')
    assert result == {"file.txt": {}}

def test_sync_audio_up(mocker):
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.listdir', return_value=['file1.mp3', 'ignore.txt'])
    
    mock_upload = mocker.patch('deploy_fetch.upload_file')
    
    deploy_fetch.sync_audio_up()
    
    # Should upload index.json + file1.mp3
    assert mock_upload.call_count == 2
    mock_upload.assert_any_call(os.path.normpath('audio/index.json'), '/home/kobazauros/mysite/audio/index.json')
    mock_upload.assert_any_call(os.path.normpath('audio/file1.mp3'), '/home/kobazauros/mysite/audio/file1.mp3')

def test_retrieve_submissions_down(mocker):
    mocker.patch('os.path.exists', side_effect=[False, False]) # Dir doesn't exist, file doesn't exist
    mocker.patch('os.makedirs')
    
    mocker.patch('deploy_fetch.list_remote_files', return_value={'sub.mp3': {}, 'other.txt': {}})
    mock_download = mocker.patch('deploy_fetch.download_file')
    
    deploy_fetch.retrieve_submissions_down()
    
    mock_download.assert_called_once()
    # Check arguments more loosely or construct expected path carefully
    args = mock_download.call_args[0]
    assert args[0] == '/home/kobazauros/mysite/submissions/sub.mp3'
    assert args[1].endswith('sub.mp3')
