import argparse
import logging
import pdb
import datetime
import os


import xarray as xr
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import cmocean
import cmdline_provenance as cmdprov


def convert_pr_units(darray):
    """Convert kg m-2 s-1 to mm day-1 and generate logs.
   
    Args:
      darray (xarray.DataArray): Precipitation data
    
    """


    darray.data = darray.data * 86400
    darray.attrs['units'] = 'mm/day'

    assert darray.data.max() < 2000, 'There is a precipitation value/s > 2000 mm/day'
    
    assert darray.data.min() >= 0.0, 'There is at least one negative precipitation value'

    return darray

def apply_mask(darray, sftlf_file, realm):
    """Mask ocean or land using a sftlf (land surface fraction) file.
   
    Args:
      darray (xarray.DataArray): Data to mask
      sftlf_file (str): Land surface fraction file
      realm (str): Realm to mask
   
    """
  
    dset = xr.open_dataset(sftlf_file)
    assert realm in ['land', 'ocean'], """valid realms are 'land' or 'ocean'"""
    if realm == 'land':
        masked_darray = darray.where(dset['sftlf'].data < 50)
    else:
        masked_darray = darray.where(dset['sftlf'].data > 50)   
   
    return masked_darray


def create_plot(clim, model, season, gridlines=False, levels=None):
    """Plot the precipitation climatology.
    
    Args:
      clim (xarray.DataArray): Precipitation climatology data
      model (str): Name of the climate model
      season (str): Season
     
    Kwargs:
      gridlines (bool): Select whether to plot gridlines
      levels (list): Tick marks on the colorbar    
    
    """

    if not levels:
        levels = np.arange(0, 13.5, 1.5)
       
    fig = plt.figure(figsize=[12,5])
    ax = fig.add_subplot(111, projection=ccrs.PlateCarree(central_longitude=180))
    clim.sel(season=season).plot.contourf(ax=ax,
                                          levels=levels,
                                          extend='max',
                                          transform=ccrs.PlateCarree(),
                                          cbar_kwargs={'label': clim.units},
                                          cmap=cmocean.cm.haline_r)
    ax.coastlines()
    if gridlines:
        plt.gca().gridlines()
    
    title = f'{model} precipitation climatology ({season})'
    plt.title(title)

def get_log_and_key(pr_file, history_attr, plot_type):
    """Get key and command line log for image metadata.
   
    Different image formats allow different metadata keys.
   
    Args:
      pr_file (str): Input precipitation file
      history_attr (str): History attribute from pr_file
      plot_type (str): File format for output image
   
    """
    
    valid_keys = {'png': 'History',
                  'pdf': 'Title',
                  'svg': 'Title',
                  'eps': 'Creator',
                  'ps' : 'Creator'}    

    assert plot_type in valid_keys.keys(), f"Image format not one of: {*[*valid_keys],}"
    log_key = valid_keys[plot_type]
    new_log = cmdprov.new_log(infile_logs={pr_file: history_attr})
    
    return log_key, new_log
    
def main(inargs):
    """Run the program."""
    var = 'pr'
    script_directory = os.path.dirname(os.path.abspath(__file__))
    script_filename = os.path.basename(__file__)
    log_directory = "log/"
    figure_directory = "figure/"
    log_filename = f"log_{script_filename.rsplit('.', 1)[0]}.txt"
    # log_filepath = os.path.join(script_directory, log_directory, log_filename)
    log_filepath = os.path.join(script_directory, log_directory, log_filename)

    figure_filepath = os.path.join(script_directory, figure_directory)
    # pdb.set_trace()
    os.makedirs(os.path.dirname(log_filepath), exist_ok=True)
    # pdb.set_trace()
    os.makedirs(os.path.dirname(figure_filepath), exist_ok=True)

    logging.basicConfig(level=logging.INFO, filename=log_filepath)
    logging.info(f"\n\n-----------------------------\n")

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"{current_time}\n")
    dset = xr.open_dataset(inargs.pr_file)
    
    logging.info(f"The maximum {var} value is {dset[var].data.max() *86400}")
    logging.info(f"The minimum {var} value is {dset[var].data.min()}")
    
    clim = dset[var].groupby('time.season').mean('time', keep_attrs=True)
    input_units = clim.attrs['units']
    if input_units == 'kg m-2 s-1':
        clim = convert_pr_units(clim)
        logging.info('Units converted from kg m-2 s-1 to mm/day')
    elif input_units == 'mm/day':
        pass
    else:
        raise ValueError("""Input units are not 'kg m-2 s-1' or 'mm/day'""")
        
        
    assert clim.data.max() < 2000, 'There is a precipitation value/s > 2000 mm/day'
    
    if inargs.mask:
        sftlf_file, realm = inargs.mask
        clim = apply_mask(clim, sftlf_file, realm)

    create_plot(clim, dset.attrs['source_id'], inargs.season,
                gridlines=inargs.gridlines, levels=inargs.cbar_levels)
    
    log_key, new_log = get_log_and_key(inargs.pr_file,
                                       dset.attrs['history'],
                                       inargs.output_file.split('.')[-1])
    
    plt.savefig(f"{figure_filepath}{inargs.output_file}", metadata={log_key: new_log}, dpi=200)    
    logging.info(f"Figure has been generated at: {figure_filepath}\nFigure name: {inargs. output_file}")
    logging.info(f"Season: {inargs.season}")
    if inargs.mask:
        logging.info(f"{inargs.mask[1].capitalize()} has been masked out.")

    
    

if __name__ == '__main__':
    description='Plot the precipitation climatology for a given season.'
    parser = argparse.ArgumentParser(description=description)
   
    parser.add_argument("pr_file", type=str, help="Precipitation data file")
    parser.add_argument("season", type=str, help="Season to plot")
    parser.add_argument("output_file", type=str, help="Output file name")

    parser.add_argument("--gridlines", action="store_true", default=False,
                        help="Include gridlines on the plot")
    parser.add_argument("--cbar_levels", type=float, nargs='*', default=None,
                        help='list of levels / tick marks to appear on the colorbar')
    parser.add_argument("--mask", type=str, nargs=2,
                        metavar=('SFTLF_FILE', 'REALM'), default=None,
                        help="""Provide sftlf file and realm to mask ('land' or 'ocean')""")

    args = parser.parse_args()

    main(args)