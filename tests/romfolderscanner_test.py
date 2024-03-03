import unittest, os
import unittest.mock
from unittest.mock import MagicMock, patch

import logging

from tests.fakes import FakeProgressDialog, random_string, FakeFile

logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.DEBUG)
logger = logging.getLogger(__name__)

from resources.lib.scanner import RomFolderScanner

from akl.api import ROMObj

class Test_romscannerstests(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):        
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'assets/'))
                
        print('ROOT DIR: {}'.format(cls.ROOT_DIR))
        print('TEST DIR: {}'.format(cls.TEST_DIR))
        print('TEST ASSETS DIR: {}'.format(cls.TEST_ASSETS_DIR))
        print('---------------------------------------------------------------------------')
    
    @patch('akl.api.client_get_source_scanner_settings')
    @patch('resources.lib.scanner.io.FileName.recursiveScanFilesInPath')
    def test_when_scanning_with_a_normal_rom_scanner_it_will_go_without_exceptions(self, recursive_scan_mock:MagicMock, api_settings_mock:MagicMock):
        
        # arrange
        recursive_scan_mock.return_value = [
           FakeFile('//fake/folder/myfile.dot'),
           FakeFile('//fake/folder/donkey_kong.zip'), 
           FakeFile('//fake/folder/tetris.zip'), 
           FakeFile('//fake/folder/thumbs.db'),
           FakeFile('//fake/folder/duckhunt.zip')]
        api_settings_mock.return_value = {
            'multidisc': False,
            'romext': 'zip',
            'scan_recursive': True
        }
        
        report_dir = FakeFile('//fake_reports/')
        target = RomFolderScanner(report_dir, random_string(10), None, 0, FakeProgressDialog())
        
        # act
        target.scan()

        # assert
        print(report_dir.getFakeContent())
    
    @patch('resources.lib.scanner.io.FileName.exists_python',autospec=True)   
    @patch('akl.api.client_get_roms_in_source')
    @patch('akl.api.client_get_source_scanner_settings')
    @patch('resources.lib.scanner.io.FileName.recursiveScanFilesInPath')
    def test_when_scanning_with_a_normal_rom_scanner_dead_roms_will_be_removed(self, 
            recursive_scan_mock:MagicMock, api_settings_mock:MagicMock, api_roms_mock:MagicMock, file_exists_mock:MagicMock):
        # arrange
        scanner_id = random_string(5)
        
        recursive_scan_mock.return_value = [
           FakeFile('//fake/folder/myfile.dot'),
           FakeFile('//fake/folder/donkey_kong.zip'), 
           FakeFile('//fake/folder/tetris.zip')]
        api_settings_mock.return_value = {
            'multidisc': False,
            'romext': 'zip',
            'scan_recursive': True
        }               
        
        roms = []
        roms.append(ROMObj({'id': '1', 'scanned_by_id': scanner_id, 'm_name': 'this-one-will-be-deleted', 'scanned_data': { 'file': '//not-existing/byebye.zip'}}))
        roms.append(ROMObj({'id': '2', 'scanned_by_id': scanner_id, 'm_name': 'this-one-will-be-deleted-too', 'scanned_data': { 'file': '//not-existing/byebye.zip'}}))
        roms.append(ROMObj({'id': '3', 'scanned_by_id': scanner_id, 'm_name': 'Rocket League', 'scanned_data': { 'file': '//fake/folder/rocket.zip'}}))
        roms.append(ROMObj({'id': '4', 'scanned_by_id': scanner_id, 'm_name': 'this-one-will-be-deleted-again', 'scanned_data': { 'file': '//not-existing/byebye.zip'}}))
        api_roms_mock.return_value = roms
        
        file_exists_mock.side_effect = lambda f: f.getPath().startswith('//fake/')
        report_dir = FakeFile('//fake_reports/')
        expected = 3

        # act
        target = RomFolderScanner(report_dir, scanner_id, None, 0, FakeProgressDialog())
        target.scan()

        # assert
        self.assertEqual(expected, target.amount_of_dead_roms())
        print(report_dir.getFakeContent())
    
    @patch('resources.lib.scanner.io.FileName.exists_python', autospec=True)    
    @patch('akl.api.client_get_roms_in_source')
    @patch('akl.api.client_get_source_scanner_settings')
    @patch('resources.lib.scanner.io.FileName.recursiveScanFilesInPath')
    def test_when_scanning_with_a_normal_rom_scanner_multidiscs_will_be_put_together(self, 
            recursive_scan_mock:MagicMock, api_settings_mock:MagicMock, api_roms_mock:MagicMock, file_exists_mock:MagicMock):
        
        # arrange
        scanner_id = random_string(5)
        
        recursive_scan_mock.return_value = [
           FakeFile('//fake/folder/zekda.zip'),
           FakeFile('//fake/folder/donkey kong (Disc 1 of 2).zip'), 
           FakeFile('//fake/folder/donkey kong (Disc 2 of 2).zip'), 
           FakeFile('//fake/folder/tetris.zip')]
        api_settings_mock.return_value = {
            'multidisc': True,
            'romext': 'zip',
            'scan_recursive': True
        }               

        roms = []
        roms.append(ROMObj({'id': '1', 'm_name': 'Rocket League', 'scanned_data': { 'file': '//fake/folder/rocket.zip'}}))      
        api_roms_mock.return_value = roms
        
        file_exists_mock.side_effect = lambda f: f.getPath().startswith('//fake/')
        report_dir = FakeFile('//fake_reports/')        
        target = RomFolderScanner(report_dir, scanner_id, None, 0, FakeProgressDialog())
        
        expected = 4

        # act
        target.scan()

        # assert
        i=0
        for rom in target.scanned_roms:
            i+=1
            print('- {} ------------------------'.format(i))
            for key, value in rom.get_data_dic().items():
                print('[{}] {}'.format(key, value))

        self.assertEqual(expected, target.amount_of_scanned_roms())
    
    @patch('resources.lib.scanner.io.FileName.exists_python', autospec=True)    
    @patch('akl.api.client_get_roms_in_source')
    @patch('akl.api.client_get_source_scanner_settings')
    @patch('resources.lib.scanner.io.FileName.recursiveScanFilesInPath')
    def test_when_scanning_with_a_normal_rom_scanner_existing_items_wont_end_up_double(self, 
            recursive_scan_mock:MagicMock, api_settings_mock:MagicMock, api_roms_mock:MagicMock, file_exists_mock:MagicMock):        
        # arrange
        scanner_id = random_string(5)
        
        recursive_scan_mock.return_value = [
           FakeFile('//fake/folder/zelda.zip'),
           FakeFile('//fake/folder/donkey kong.zip'), 
           FakeFile('//fake/folder/tetris.zip')]
        api_settings_mock.return_value = {
            'multidisc': False,
            'romext': 'zip',
            'scan_recursive': True
        }  
         
        roms = []
        roms.append(ROMObj({'id': '1','scanned_by_id': scanner_id, 'm_name': 'Rocket League', 'scanned_data': { 'file':'//fake/folder/rocket.zip'}}))
        roms.append(ROMObj({'id': '2','scanned_by_id': scanner_id, 'm_name': 'Zelda', 'scanned_data': { 'file': '//fake/folder/zelda.zip'}}))
        roms.append(ROMObj({'id': '3','scanned_by_id': scanner_id, 'm_name': 'Tetris', 'scanned_data': { 'file': '//fake/folder/tetris.zip'}}))
        api_roms_mock.return_value = roms
        
        file_exists_mock.side_effect = lambda f: f.getPath().startswith('//fake/')
        report_dir = FakeFile('//fake_reports/')        
        target = RomFolderScanner(report_dir, scanner_id, None, 0, FakeProgressDialog())
        
        expected = 1 # only donkey kong.zip is new

        # act
        target.scan()

        # assert
        i=0
        for rom in target.scanned_roms:
            i+=1
            print('- {} ------------------------'.format(i))
            for key, value in rom.get_data_dic().items():
                print('[{}] {}'.format(key, value))

        self.assertEqual(expected, target.amount_of_scanned_roms())
        
    @patch('resources.lib.scanner.io.FileName.exists_python', autospec=True)    
    @patch('akl.api.client_get_roms_in_source')
    @patch('akl.api.client_get_source_scanner_settings')
    @patch('resources.lib.scanner.io.FileName.recursiveScanFilesInPath')
    def test_when_scanning_with_a_normal_rom_scanner_and_bios_roms_must_be_skipped_they_wont_be_added(self,
            recursive_scan_mock:MagicMock, api_settings_mock:MagicMock, api_roms_mock:MagicMock, file_exists_mock:MagicMock):
        # arrange
        scanner_id = random_string(5)
        
        recursive_scan_mock.return_value = [
           FakeFile('//fake/folder/zelda.zip'),
           FakeFile('//fake/folder/donkey kong.zip'), 
           FakeFile('//fake/folder/[BIOS] dinkytoy.zip'), 
           FakeFile('//fake/folder/tetris.zip')]
        api_settings_mock.return_value = {
            'multidisc': False,
            'romext': 'zip',
            'scan_recursive': True
        }  
         
        roms = []
        roms.append(ROMObj({'id': '1','scanned_by_id': scanner_id, 'm_name': 'Rocket League', 'scanned_data': { 'file': '//fake/folder/rocket.zip'}}))
        roms.append(ROMObj({'id': '2','scanned_by_id': scanner_id, 'm_name': 'Zelda', 'scanned_data': { 'file': '//fake/folder/zelda.zip'}}))
        roms.append(ROMObj({'id': '3','scanned_by_id': scanner_id, 'm_name': 'Tetris', 'scanned_data': { 'file': '//fake/folder/tetris.zip'}}))
        api_roms_mock.return_value = roms
        
        file_exists_mock.side_effect = lambda f: f.getPath().startswith('//fake/')
        report_dir = FakeFile('//fake_reports/')        
        target = RomFolderScanner(report_dir, scanner_id, None, 0, FakeProgressDialog())
        
        expected = 1 # donkey kong.zip is only new ROM

        # act
        target.scan()

        # assert
        i=0
        for rom in target.scanned_roms:
            i+=1
            print('- {} ------------------------'.format(i))
            for key, value in rom.get_data_dic().items():
                print('[{}] {}'.format(key, value))

        self.assertEqual(expected, target.amount_of_scanned_roms())

if __name__ == '__main__':    
    unittest.main()
