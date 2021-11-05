import unittest, os
import unittest.mock
from unittest.mock import MagicMock, patch

import logging

from fakes import FakeProgressDialog, random_string, FakeFile

logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.DEBUG)
logger = logging.getLogger(__name__)

from resources.lib.scraper import LocalFilesScraper
from ael.scrapers import ScrapeStrategy, ScraperSettings

from ael.api import ROMObj
from ael import constants

class Test_localfilesscraper(unittest.TestCase):
    
    ROOT_DIR = ''
    TEST_DIR = ''
    TEST_ASSETS_DIR = ''

    @classmethod
    def setUpClass(cls):        
        cls.TEST_DIR = os.path.dirname(os.path.abspath(__file__))
        cls.ROOT_DIR = os.path.abspath(os.path.join(cls.TEST_DIR, os.pardir))
        cls.TEST_ASSETS_DIR = os.path.abspath(os.path.join(cls.TEST_DIR,'assets/'))
                
        logger.info('ROOT DIR: {}'.format(cls.ROOT_DIR))
        logger.info('TEST DIR: {}'.format(cls.TEST_DIR))
        logger.info('TEST ASSETS DIR: {}'.format(cls.TEST_ASSETS_DIR))
        logger.info('---------------------------------------------------------------------------')

    @patch('ael.api.client_get_rom')
    def test_scraping_metadata_for_game(self, api_rom_mock: MagicMock):        
        
        # arrange        
        settings = ScraperSettings()
        settings.scrape_metadata_policy = constants.SCRAPE_POLICY_NFO_PREFERED
        settings.scrape_assets_policy = constants.SCRAPE_ACTION_NONE
                        
        rom_id = random_string(5)
        rom = ROMObj({
            'id': rom_id,
            'scanned_data': {
                'file': Test_localfilesscraper.TEST_ASSETS_DIR + '\\dr_mario.zip'
            }
        })
        api_rom_mock.return_value = rom
        #with open(Test_nfo_scraper.TEST_ASSETS_DIR + "\\dr_mario.nfo", 'r') as f:
        #    fakeRomPath.setFakeContent(f.read())

        target = ScrapeStrategy(None, 0, settings, LocalFilesScraper(), FakeProgressDialog())
                        
        # act
        actual = target.process_single_rom(rom_id)
                
        # assert
        self.assertTrue(actual)
        self.assertEqual(u'Dr. Mario', actual.get_name())
        self.assertEqual(u'Puzzle', actual.get_genre())
        logger.info(actual.get_data_dic())
        
    @patch('ael.api.client_get_rom')
    def test_when_scraping_with_nfoscraper_it_will_give_the_correct_result(self, api_rom_mock: MagicMock):    
    
        # arrange        
        settings = ScraperSettings()
        settings.scrape_metadata_policy = constants.SCRAPE_POLICY_NFO_PREFERED
        settings.scrape_assets_policy = constants.SCRAPE_ACTION_NONE
                
        rom_id = random_string(5)
        rom = ROMObj({
            'id': rom_id,
            'scanned_data': {
                'file':  Test_localfilesscraper.TEST_ASSETS_DIR + '\\pitfall.zip'
            }
        })
        api_rom_mock.return_value = rom
        
        expected = 'Pitfall: The Mayan Adventure'        
        target = ScrapeStrategy(None, 0, settings, LocalFilesScraper(), FakeProgressDialog())
                        
        # act
        actual = target.process_single_rom(rom_id)
                
        # assert
        self.assertTrue(actual)
        self.assertEqual(expected, actual.get_name())
        logger.info(actual.get_data_dic())
        
    @patch('ael.utils.io.FileName.scanFilesInPath')
    @patch('ael.api.client_get_rom')
    def test_when_scraping_local_assets_it_will_give_the_correct_result(self, api_rom_mock:MagicMock, file_mock:MagicMock):
        # arrange
        file_mock.return_value = [FakeFile('x.jpg'),FakeFile('y.jpg'), FakeFile('pitfall.jpg'), FakeFile('donkeykong.jpg')]

        settings = ScraperSettings()
        settings.scrape_metadata_policy = constants.SCRAPE_ACTION_NONE
        settings.scrape_assets_policy = constants.SCRAPE_POLICY_SCRAPE_ONLY
        settings.asset_IDs_to_scrape = [constants.ASSET_TITLE_ID]
              
        rom_id = random_string(5)
        rom = ROMObj({
            'id': rom_id,
            'scanned_data': {
                'identifier': 'Pitfall',
                'file': '/roms/Pitfall.zip'
            },
            'platform': 'Sega 32X',
            'assets': {key: '' for key in constants.ROM_ASSET_ID_LIST},
            'asset_paths': {
                constants.ASSET_TITLE_ID: '/titles/',
            }
        })
        api_rom_mock.return_value = rom
        
        expected = '/titles/Pitfall.jpg'
        target = ScrapeStrategy(None, 0, settings, LocalFilesScraper(), FakeProgressDialog())  
                               
        # act
        actual = target.process_single_rom(rom_id)
                
        # assert
        self.assertTrue(actual) 
        logger.info(actual.get_data_dic()) 
        
        self.assertTrue(actual.entity_data['assets'][constants.ASSET_TITLE_ID], 'No title defined')
        self.assertEquals(actual.entity_data['assets'][constants.ASSET_TITLE_ID], expected)
        
    # def test_scraping_metadata_for_game(self):
        
    #     # arrange
    #     target = LocalFilesScraper()

    #     # act
    #     candidates = target.get_candidates('doctor mario', io.FileName('/doctor mario.zip'), None, 'Nintendo NES', {})
    #     actual = target.get_metadata(candidates[0])
                          
    #     # assert
    #     self.assertFalse(actual)
    #     logger.info(actual)

    # @patch('resources.scrap.misc_add_file_cache')
    # @patch('resources.scrap.misc_search_file_cache', side_effect = mocked_cache_search)
    # def test_scraping_assets_for_game(self, cache_mock, search_cache_mock):

    #     # arrange
    #     settings = self.get_test_settings()
    #     target = LocalFilesScraper()
        
    #     assets_to_scrape = [
    #         g_assetFactory.get_asset_info(ASSET_BOXFRONT_ID), 
    #         g_assetFactory.get_asset_info(ASSET_BOXBACK_ID), 
    #         g_assetFactory.get_asset_info(ASSET_SNAP_ID)]
        
    #     # launcher = StandardRomLauncher(None, settings, None, None, None, None, None)
    #     # launcher.set_platform('Nintendo SNES')
    #     # launcher.set_asset_path(g_assetFactory.get_asset_info(ASSET_BOXFRONT_ID),'/my/nice/assets/front/')
    #     # launcher.set_asset_path(g_assetFactory.get_asset_info(ASSET_BOXBACK_ID),'/my/nice/assets/back/')
    #     # launcher.set_asset_path(g_assetFactory.get_asset_info(ASSET_SNAP_ID),'/my/nice/assets/snaps/')
        
    #     # rom = ROM({'id': 1234})
    #     # fakeRomPath = FakeFile('/my/nice/roms/castlevania.zip')

    #     # act
    #     actuals = []
    #     candidates = target.get_candidates('doctor mario', io.FileName('/doctor mario.zip'), None, 'Nintendo NES', {})
    #     for asset_to_scrape in assets_to_scrape:
    #         an_actual = target.get_assets(candidates[0], asset_to_scrape)
    #         actuals.append(an_actual)
                
    #     # assert
    #     for actual in actuals:
    #         self.assertFalse(actual)
        
    #     print(actuals)