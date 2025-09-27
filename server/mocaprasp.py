# tells the shell to use python 3 so you can run ./mocaprasp.py directly
#!/usr/bin/env python3 
# handles filesystem operaitions (making diretories, joining paths)
import os 

# library for serializing and deserializing python objects 
# serializing (pickling) is converting a python object into a byte stream to transport over the network
# deserializing (unpickling)  converts byte stream back into pyton object
import pickle 

from datetime import datetime #library for getting timestamps

# library for making command line tools
# users use these tools by typing text commands into terminal to perform tasks
import click 

#import three classes from the mcr.capture package that run different MoCap processes
#CEC = Camera Extrinsics Calibration
from mcr.capture.CEC import CEC 
#GPE = Ground Plane Estimation
from mcr.capture.GPE import GPE
#SCR = Standard Capture Routine
from mcr.capture.SCR import SCR 


@click.group() # command group
def mocaprasp():
    """
    MoCap Rasp - Optical Tracking Arena\n\n
    Server script for the MoCap system at the Erobotica Lab, UFCG.\n
    Please use it together with the corresponding client script.
    """
    pass # function just organizes subcommands


@click.command(name="cec") # camera extrinsics calibration subcommand
@click.option(
    "--cameraids",
    "-c",
    default="1,2,3",# camera IDs
    help="List of active camera IDs (Default: 1,2,3)",
)
@click.option(
    #number of relfective marker tracked
    "--markers", "-m", default=3, help="Number of expected markers (Default: 3)"
)
@click.option(
    # small delay before recording starts
    "--trigger", "-t", default=10, help="Trigger time in seconds (Default: 10)"
)
@click.option(
    #recording duration in seconds
    "--record", "-r", default=360, help="Recording time in seconds (Default: 360)"
)
#output data interpolation in frames per second
@click.option("--fps", "-f", default=100, help="Interpolation FPS (Default: 100)")
#shows deubbing and processing info
@click.option(
    "--verbose", "-v", is_flag=True, help="Show ordering and interpolation verbosity"
)
#saves raw data to CSV files
@click.option("--save", "-s", is_flag=True, help="Save received packages to CSV")
#parameters for DBSCAN clustering algorithim (used for filtering noisy 3D points)
@click.option("--dbscan-eps", default=0.01, help="DBSCAN epsilon for clustering")
@click.option(
    "--dbscan-min-samples", default=10, help="DBSCAN minimum samples for clustering"
)
@click.option(
    "--use-clustering",
    is_flag=True,
    help="Enable 3D clustering for consensus filtering",
)
#get new camera data
@click.option(
    "--collect", is_flag=True, help="Run in collection mode only (no calibration)"
)
#load data into csv files and perform calibration
@click.option(
    "--calibrate",
    type=click.Path(exists=True),
    help="Run in calibration-only mode using saved CSV file",
)
def cec(        # cec func parameters
    cameraids,
    markers,
    trigger,
    record,
    fps,
    verbose,
    save,
    dbscan_eps,
    dbscan_min_samples,
    use_clustering,
    collect,
    calibrate,
):
    #user documentation
    """
    Camera Extrinsics Calibration
    Use either --collect or --calibrate:
    --collect    → Collect raw 2D data from cameras and save
    --calibrate  → Load CSV and compute extrinsics (no live capture)
    """
    #ensures users chose one mode collect or calibrate not both and not none
    if collect and calibrate:
        click.echo("⚠️  You cannot specify both --collect and --calibrate.")
        click.echo("Example: python3 mocaprasp.py cec --collect")
        click.echo("         python3 mocaprasp.py cec --calibrate path/to/file.csv")
        return
    elif not collect and not calibrate:
        click.echo("⚠️  You must specify either --collect or --calibrate.")
        click.echo("Example: python3 mocaprasp.py cec --collect")
        click.echo("         python3 mocaprasp.py cec --calibrate path/to/file.csv")
        return
    # create a CEC object (the class that runs calibration)
    cecServer = CEC(
        cameraids,
        markers,
        trigger,
        record,
        fps,
        verbose,
        save,
        dbscan_eps,
        dbscan_min_samples,
        use_clustering,
    )
    #collecting new data condition
    if collect:
        cecServer.connect() # connect to cameras
        cecServer.collect() # start gathering marker data

        ymd, now = datetime.now().strftime("%y-%m-%d"), datetime.now().strftime( # time stampts data
            "%H-%M-%S"
        )
        out_dir = "debug/dataSaves/" + ymd + "/" # saves entire cecServer object as a pickle file (.pkl)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"CEC-{now}.pkl")
        with open(out_path, "wb") as f:
            pickle.dump(cecServer, f)
        click.echo(f"✅ CEC data saved to {out_path}")
    #calibrating existing data
    if calibrate:
        # load either a .pkl (pickle file) or .csv (raw camera data)
        if calibrate.endswith(".pkl"):
            with open(calibrate, "rb") as f:
                cecServer = pickle.load(f)
            cecServer.calibrate(datapath=None) # compute extrinsic calibration (relative camera positions/orientations)
        elif calibrate.endswith(".csv"):
            cecServer = CEC(
                cameraids,
                markers,
                trigger,
                record,
                fps,
                verbose,
                save,
                dbscan_eps,
                dbscan_min_samples,
                use_clustering,
            )
            cecServer.calibrate(datapath=calibrate) # compute extrinsic calibration
        else:
            click.echo("❌ Unsupported file type. Use .pkl or .csv")
        click.echo("✅ Camera extrinsics calibration completed.")

# similart setting to cec subcommand
@click.command(name="gpe") # group plane estimation subcommand
@click.option(
    "--cameraids",
    "-c",
    default="1,2,3",
    help="List of active camera IDs (Default: 1,2,3)",
)
@click.option(
    "--markers", "-m", default=3, help="Number of expected markers (Default: 3)"
)
@click.option("--trigger", "-t", default=2, help="Trigger time in seconds (Default: 2)")
@click.option(
    "--record", "-r", default=10, help="Recording time in seconds (Default: 10)"
)
@click.option("--fps", "-f", default=100, help="Interpolation FPS (Default: 100)")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show ordering and interpolation verbosity"
)
@click.option("--save", "-s", is_flag=True, help="Save received packages to CSV")
@click.option(
    "--collect", is_flag=True, help="Run in collection mode only (no estimation)"
)
@click.option(
    "--estimate",
    type=click.Path(exists=True),
    help="Run ground plane estimation using a saved CSV file",
)
def gpe(cameraids, markers, trigger, record, fps, verbose, save, collect, estimate):
    """
    Ground Plane Estimation\n\n
    - Place 3 non-collinear markers in the calibration wand;\n
    - Put it at the center of the capture volume;\n
    - Make sure they are levelled with each other.\n\n
    The default options are already adjusted for this process.
    Use either --collect or --estimate:
    --collect    → Collect raw 2D data from cameras and save
    --estimate   → Load CSV and compute ground plane (no live capture)
    """
    if collect and estimate: # can only perform data collection or estimation not both
        click.echo("❌ Cannot use --collect and --estimate together.")
        click.echo("Example: python3 mocaprasp.py gpe --collect")
        click.echo("         python3 mocaprasp.py gpe --estimate path/to/file.csv")
        return
    elif not collect and not estimate:
        click.echo("❌ You must specify either --collect or --estimate.")
        click.echo("Example: python3 mocaprasp.py gpe --collect")
        click.echo("         python3 mocaprasp.py gpe --estimate path/to/file.csv")
        return

    gpeServer = GPE(cameraids, markers, trigger, record, fps, verbose, save)
    # collects and saves data
    if collect:
        gpeServer.connect()
        gpeServer.collect()

        ymd, now = datetime.now().strftime("%y-%m-%d"), datetime.now().strftime(
            "%H-%M-%S"
        )
        out_dir = "debug/dataSaves/" + ymd + "/"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"GPE-{now}.pkl")
        with open(out_path, "wb") as f:
            pickle.dump(gpeServer, f)
        click.echo(f"✅ GPE data saved to {out_path}")
    #peforms ground plane estimation fiven a .pkl or .csv file
    if estimate:
        if estimate.endswith(".pkl"):
            with open(estimate, "rb") as f:
                gpeServer = pickle.load(f)
            gpeServer.estimate(datapath=None)
        elif estimate.endswith(".csv"):
            gpeServer = GPE(cameraids, markers, trigger, record, fps, verbose, save)
            gpeServer.estimate(datapath=estimate)
        else:
            click.echo("❌ Unsupported file type. Use .pkl or .csv")
        click.echo("✅ Ground plane estimation completed.")


@click.command(name="scr") #standard capture routine subcommand
@click.option(
    "--cameraids",
    "-c",
    default="1,2,3",
    help="List of active camera IDs (Default: 1,2,3)",
)
@click.option(
    "--markers", "-m", default=3, help="Number of expected markers (Default: 3)"
)
@click.option("--trigger", "-t", default=5, help="Trigger time in seconds (Default: 5)")
@click.option(
    "--record", "-r", default=30, help="Recording time in seconds (Default: 30)"
)
@click.option("--fps", "-f", default=100, help="Interpolation FPS (Default: 100)")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show ordering and interpolation verbosity"
)
@click.option("--save", "-s", is_flag=True, help="Save received packages to CSV")
#THE MAIN CAPTURE ROUTINE; used after calibration (CEC) and plane estimation (GPE)
def scr(cameraids, markers, trigger, record, fps, verbose, save):
    """
    Standard Capture Routine\n\n
    - Routines required to be done previously at least once:\n
        1. CEC;\n
        2. GPE.\n
    - With CEC and GPE routines done, execute SCR as much as you like;\n\n
    Adjust the options to match your desired capture.
    """
    # connect to cameras and peforms recording session
    scrServer = SCR(cameraids, markers, trigger, record, fps, verbose, save)
    scrServer.connect()
    scrServer.collect()

# register subcommands to the mocaprasp command line interface group
mocaprasp.add_command(cec)
mocaprasp.add_command(scr)
mocaprasp.add_command(gpe)
#SCRIPT ENTRY POINT
if __name__ == "__main__": # runs command line interace when script is execute directly
    mocaprasp()
#########

#CEC#
#teaches the system how the rasp cameras are arrange by mapping out the position/angle
# -- collect runs a hort test and --calibrate uses the test to figure out the configuration
#GPE#
#tells the systems where the floor/ground is in the capture area
# -- collect makes camrea record 3 marker places flat and --estimate figures out where the ground is in the 3d map
#SCR#
#captures real motion once setup is done
# --record 60 tells the camrea to connect, wait a moment, then record for 60 seconds then the data is saved
# data is a 3D recording