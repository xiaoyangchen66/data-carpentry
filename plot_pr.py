import xarray as xr
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import cmocean
import argparse


def convert_pr_units(darray):
    """Convert kg m-2 s-1 to mm day-1.
    
    Args:
      darray (xarray.DataArray): Precipitation data
    
    """
    
    darray.data = darray.data * 86400
    darray.attrs['units'] = 'mm/day'
    
    return darray


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


def main(inargs):
    """Run the program."""

    dset = xr.open_dataset(inargs.pr_file)
    
    clim = dset['pr'].groupby('time.season').mean('time', keep_attrs=True)
    clim = convert_pr_units(clim)

    create_plot(clim, dset.attrs['source_id'], inargs.season, gridlines=inargs.gridlines, levels=inargs.cbar)
    plt.savefig(inargs.output_file, dpi=200)


if __name__ == '__main__':
    print("This script is being run as the main program.")
    print(f"Running '{__file__}'")
    description='Plot the precipitation climatology.'
    parser = argparse.ArgumentParser(description=description)
    
    parser.add_argument("pr_file", type=str, help="Precipitation data file")
    parser.add_argument("season", type=str, help="Season to plot", choices=['MAM','JJA','SON','DJF'])
    parser.add_argument("output_file", type=str, help="Output file name")
    parser.add_argument("-g", "--gridlines", action="store_true", default=False, help="Include gridlines on the plot")
    parser.add_argument('-cbar', type=float, nargs='*', default=None, help='list of levels / tick marks to appear on the colorbar')
    args = parser.parse_args()
    
    main(args)





