import os
import sys 
from pystac import Catalog, Collection, Item, MediaType, Asset, CatalogType, TemporalExtent, Extent, SpatialExtent
import gdal
import numpy as np
import datetime
from .helpers import *
import logging
import click
import shutil
from .stac import S2_stac_item
from shapely.geometry import Polygon, mapping, shape
from shapely.ops import cascaded_union


gdal.UseExceptions()

logging.basicConfig(stream=sys.stderr, 
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S')

workflow = dict([('id', 'burned-area'),
                ('label', 'Sentinel-2 burned area'),
                ('doc', 'Sentinel-2 burned area with NDVI/NDWI threshold')])


ndvi_threshold = dict([('id', 'ndvi_threshold'),
                       ('value', '0.19'),
                       ('label', 'NDVI difference threshold'),
                       ('doc', 'NDVI difference threshold'),
                       ('type', 'string')])

ndwi_threshold = dict([('id', 'ndwi_threshold'),
                       ('value', '0.18'),
                       ('label', 'NDWI difference threshold'),
                       ('doc', 'NDWI difference threshold'),
                       ('type', 'string')])
    
pre_event = dict([('id', 'pre_event'),
                  ('label', 'Sentinel-2 Level-2A pre-event'),
                  ('doc', 'Sentinel-2 Level-2A pre-event acquisition'),
                  ('value', 'https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_36RTT_20191205_0_L2A'), 
                  ('type', 'string')])

post_event = dict([('id', 'post_event'),
                  ('label', 'Sentinel-2 Level-2A post-event'),
                  ('doc', 'Sentinel-2 Level-2A post-event acquisition'),
                  ('value', 'https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_36RTT_20191215_0_L2A'), 
                  ('type', 'string')])


@click.command()
@click.option('--pre_event',
              'e_pre_event', 
              help=pre_event['doc'])
@click.option('--post_event', 
              'e_post_event',
              help=post_event['doc'])
@click.option('--ndvi_threshold',
              'e_ndvi_threshold', 
              default=0.19,
              help=ndvi_threshold['doc'])
@click.option('--ndwi_threshold',
              'e_ndwi_threshold', 
              default=0.18, 
              help=ndwi_threshold['doc'])
def entry(e_pre_event, e_post_event, e_ndvi_threshold, e_ndwi_threshold):
    
    ndvi_threshold['value'] = e_ndvi_threshold
    ndwi_threshold['value'] = e_ndwi_threshold
    pre_event['value'] = e_pre_event  
    post_event['value'] = e_post_event
    
    main(ndvi_threshold, ndwi_threshold, pre_event, post_event)

def main(ndvi_threshold, ndwi_threshold, pre_event, post_event):

    os.environ['PREFIX']='/opt/anaconda/envs/env_burned_area'
    
    os.environ['PROJ_LIB'] = os.path.join(os.environ['PREFIX'], 'share/proj')
    os.environ['GDAL_DATA'] = os.path.join(os.environ['PREFIX'], 'share/gdal')

    s2_item_pre = S2_stac_item(pre_event['value'])
    s2_item_post = S2_stac_item(post_event['value'])
    
    s2_items = dict()
    s2_items['pre-event'] = S2_stac_item(pre_event['value'])
    s2_items['post-event'] = S2_stac_item(post_event['value'])
    
    dates = []
    bboxes = []
    
    for index, item in enumerate([s2_item_pre.item, s2_item_post.item]):
        
        dates.append(item.datetime)
        bboxes.append(shape(item.geometry).bounds)
        
        logging.info('Stacking bands for input {}'.format(item.id))
        vrt_bands = []

        for band in ['B04', 'B08', 'B11', 'SCL']:

            vrt_bands.append('/vsicurl/{}'.format(item.assets[band].get_absolute_href()))

        vrt = '{}.vrt'.format('pre_event' if index == 0 else 'post_event')
        tif = '{}.tif'.format('pre_event' if index == 0 else 'post_event')

        logging.info('Build vrt for {}'.format(item.id))

        ds = gdal.BuildVRT(vrt,
                           vrt_bands,
                           srcNodata=0,
                           xRes=10, 
                           yRes=10,
                           separate=True)
        ds.FlushCache()


        logging.info('Translate {}'.format(item.id))

        gdal.Translate(tif,
                       vrt,
                       outputType=gdal.GDT_UInt16)

        os.remove(vrt)
    
    ds = gdal.Open('pre_event.tif')

    pre_b04 = ds.GetRasterBand(1).ReadAsArray()
    pre_b08 = ds.GetRasterBand(2).ReadAsArray()
    pre_b11 = ds.GetRasterBand(3).ReadAsArray()
    pre_scl = ds.GetRasterBand(4).ReadAsArray()

    ds = None

    os.remove('pre_event.tif')

    ds = gdal.Open('post_event.tif')

    post_b04 = ds.GetRasterBand(1).ReadAsArray()
    post_b08 = ds.GetRasterBand(2).ReadAsArray()
    post_b11 = ds.GetRasterBand(3).ReadAsArray()
    post_scl = ds.GetRasterBand(4).ReadAsArray()

    width = ds.RasterXSize
    height = ds.RasterYSize

    input_geotransform = ds.GetGeoTransform()
    input_georef = ds.GetProjectionRef()

    ds = None

    os.remove('post_event.tif')
    
    gain = 10000

    pre_ndwi2 = (pre_b08 / gain - pre_b11 / gain) / (pre_b08 / gain  + pre_b11 / gain)
    post_ndwi2 = (post_b08 / gain - post_b11 / gain) / (post_b08 / gain + post_b11 / gain)

    pre_b11 = None
    post_b11 = None

    pre_ndvi = (pre_b08 / gain - pre_b04 / gain) / (pre_b08 / gain  + pre_b04 / gain)
    post_ndvi = (post_b08 / gain - post_b04 / gain) / (post_b08 / gain + post_b04 / gain)

    pre_b04 = None
    post_b04 = None

    pre_b08 = None
    post_b08 = None

    conditions = (((post_ndwi2 - pre_ndwi2) > float(ndwi_threshold['value'])) & ((post_ndvi - pre_ndvi) > float(ndvi_threshold['value'])) & (pre_scl == 4) | (post_scl == 4))  

    burned = np.zeros((height, width), dtype=np.uint8) 

    burned[conditions] = 1

    pre_ndwi2 = None
    post_ndwi2 = None

    pre_ndvi = None
    post_ndvi = None

    burned[np.where((pre_scl == 0) | (post_scl == 0) | (pre_scl == 1) | (post_scl == 1) | (pre_scl == 5) | (post_scl == 5) | (pre_scl == 6) | (post_scl == 6) | (pre_scl == 7) | (post_scl == 7) | (pre_scl == 8) | (post_scl == 8) | (pre_scl == 9) | (post_scl == 9))] = 2 
    
    
    logging.info('Write output product')
    
    output_name = 'S2_BURNED_AREA_{}'.format('_'.join([d.strftime("%Y%m%d") for d in dates])) 

    write_tif(burned, '{}.tif'.format(output_name), width, height, input_geotransform, input_georef)

    logging.info('Output catalog')

    catalog = Catalog(id='catalog', description='Results')

    catalog.clear_items()
    catalog.clear_children()

    result_titles = dict()

    result_titles[output_name] = {'title': 'Burned area analysis from Sentinel-2',
                                  'media_type': MediaType.COG}



    items = []

    for key, value in result_titles.items():

        result_item = Item(id=key,
                           geometry=s2_items['pre-event'].item.geometry,
                           bbox=s2_items['pre-event'].item.bbox,
                           datetime=s2_items['pre-event'].item.datetime,
                           properties={})

        result_item.add_asset(key='data',
                              asset=Asset(href='./{}.tif'.format(key), 
                              media_type=value['media_type'], 
                              title=value['title']))

        items.append(result_item)

    #collection.add_items(items)

    catalog.add_items(items)

    catalog.describe()

    catalog.normalize_and_save(root_href='./',
                               catalog_type=CatalogType.SELF_CONTAINED)

    
    shutil.move('{}.tif'.format(output_name), 
            os.path.join('./',
                         output_name,
                         '{}.tif'.format(output_name)))
    
if __name__ == '__main__':
    entry()

            

    




