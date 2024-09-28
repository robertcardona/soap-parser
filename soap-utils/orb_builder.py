"""Orb Builder

This file contains functions related to building an orb file than can be 
    fed into SOAP to generate specified reports.
"""
import orb_parser as op
import os_utils as osu

from datetime import date
from itertools import combinations
from pathlib import Path
from urllib.request import urlopen

from sgp4.api import Satrec
from sgp4 import exporter, omm

import pandas as pd
import random

base_path = Path(__file__).parent.parent
# print(f"{base_path = }")

TODAY = date.today()

def update_tle_sources(group: str, ext: str) -> None:
    """
    This function is used to update the satellite sources from the celestrak 
        website.

    Parameters
    ----------
    group : str
        This specifies the group of satellites to be downloaded.
            Must match the celestrak group labels.
    
    ext : str
        This specifies the extension the data should be in.
            Namely `tle` or `csv`.
    """
    celestrak = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT={ext}"
    data = urlopen(celestrak).read().decode('utf-8')
    with open(base_path / "data" / ext / f"{group}.{ext}", "w") as f:
        f.write(data)

if __name__ == "__main__" and False:
    update_tle_sources("tdrss", "csv")
    update_tle_sources("starlink", "csv")
    update_tle_sources("geo", "csv")

def has_duplicate_sources(filepath: str) -> bool:
    """
    This function checks for duplicate satellite names.
    If duplicates exist, there could be errors in the SOAP output and 
        analysis files.

    The source TLE `.csv` files are obtained from 
        `https://celestrak.org/NORAD/elements/`
        by selecting the `.csv` format.

    Parameters
    ----------
    filepath : str
        A filepath to a TLE `.csv` file.

    Returns
    -------
    bool
        Returns `True` if there are any duplicates and `False` otherwise.

    """
    csv_data = pd.read_csv(filepath)

    names = [name for name in csv_data["OBJECT_NAME"]]

    return len(names) != len(list(set(names)))

if __name__ == "__main__":
    # tle_sources_dupes.csv has "TIMED" as an entry twice
    assert has_duplicate_sources(base_path / "data/csv/_tdrss.csv")

    # for rest of the unit tests
    csv_data = pd.read_csv(base_path / "data/csv/tdrss.csv").astype(str)

def add_base(d: date) -> str:
    """
    This function loads in the base orb file and sets some of the key variables.

    Parameters
    ----------
    d : date
        A python date object to specify the year, month, date for the orb file
            to be set to.
    
    Returns
    -------
    str
        The base orb file with the variables set as specified.
    """
    # text = osu.read_file(base_path / "data/templates/base.orb")
    text = osu.read_file(base_path / "data/templates/base_v15.orb")
    text = text.format(
        batchmode = "ON",
        warnings = "OFF",
        year = d.year,
        month = d.month,
        day = d.day,
        hour = "0.0",
        minute = "0.0",
        second = "0.0"
    )
    return text

def create_norad_platform(
    object_name: str,
    norad_cat_id: str,
    epoch_year: str,
    epoch_fraction: str,
    mean_motion_dot: str,
    mean_motion_ddot: str,
    bstar: str,
    ephemeris_type: str,
    element_set_no: str,
    inclination: str,
    ra_of_asc_node: str,
    eccentricity: str,
    arg_of_pericenter: str,
    mean_anomaly: str,
    mean_motion: str,
    rev_at_epoch: str
) -> dict:
    """
    This function creates a dictionary object used to fill in the 
        `platform_norad.orb` template. The source for the parameters are the 
        celestrak `.tle` or `.csv` formats for TLE's. (The parameters are 
        assumed to be strings since they are only used to populate the template 
        files and not used in calculations. If necessary these can be modifed 
        to be the proper types without affecting other code.)

    Parameters
    ----------
    object_name : str
        This is the name of the platform which will be used for reference in 
            SOAP.
        `DEFINE PLATFORM NORAD "{object_name}"`

    norad_cat_id : str
        This is the Satellite Catalog Number and is crurently five digits.
    epoch_year : str
        These are the last two digits of the year.
    epoch_fraction : str
        This is the day of the year and the fractional portion of the day,
            separated by a period. For example `264.51782528` means 
            day = 264, hour = 12, minute = 25, second = 40.104192.
    mean_motion_dot : str
        The first deriavtive of mean motion; the ballistic coefficient.
    mean_motion_ddot : str
        The second derivative of mean motion (decimal point assumed).
    bstar : str
        The drag term, or radiation pressure coefficient    
            (decimal point assumed).
    ephemeris_type : str
        Always zero; only used in undistributed TLE data.
    element_set_no : str
        Incremnted when a new TLE is generated for this object.

    inclination : str
        Inclination (in degrees).
    ra_of_asc_node : str
        Right ascension of the ascending node (in degrees).
    eccentricity : str
        Eccentricity (decimal point assumed).
    arg_of_pericenter : str
        Argument of perigee (in degrees).
    mean_anomaly : str
        Mean anomaly (in degrees).
    mean_motion : str
        Mean motion (revolutions per day).
    rev_at_epoch : str
        Revolution number at epoch (revolutions).
    
    Returns
    -------
    obj : dict:
        This is a dictionary matching the corresponding keys and values.

        This is used to fill in the template `platform_norad.orb` by using
            `content.format(**obj)`with `content` the text of the template.
    """
    platform = {}

    # ISS (ZARYA)
    # 1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
    # 2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537

    platform["object_name"] = object_name               # ISS (ZARYA)
    platform["norad_cat_id"] = norad_cat_id             # 25544
    platform["epoch_year"] = epoch_year                 # 08
    platform["epoch_fraction"] = epoch_fraction         # 264.51782528
    platform["mean_motion_dot"] = mean_motion_dot       # -.00002182
    platform["mean_motion_ddot"] = mean_motion_ddot     # 00000-0
    platform["bstar"] = bstar                           # -11606-4
    platform["ephemeris_type"] = ephemeris_type         # 0
    platform["element_set_no"] = element_set_no         # 292
    platform["inclination"] = inclination               # 51.6416
    platform["ra_of_asc_node"] = ra_of_asc_node         # 247.4627
    platform["eccentricity"] = eccentricity             # 0006703
    platform["arg_of_pericenter"] = arg_of_pericenter   # 130.5360
    platform["mean_anomaly"] = mean_anomaly             # 325.0288
    platform["mean_motion"] = mean_motion               # 15.72125391
    platform["rev_at_epoch"] = rev_at_epoch             # 56353
    
    return platform

def create_custom_platform(
    system: str,
    object_name: str,
    body: str,
    ic_type: str,
    orbit_type: str,
    semi_major_axis: str,
    eccentricity: str,
    inclination: str,
    ra_of_asc_node: str,
    arg_of_pericenter: str,
    mean_anomaly: str,
    year: str,
    month: str,
    day: str,
    hour: str,
    minute: str,
    second: str
) -> dict:
    """
    This function creates a dictionary object used to fill in the 
        `platform_custom.orb` template. This function is used when the 
        desired platform is not available in TLE format. 
        For example, Moon or Mars satellites.

    Parameters
    ----------
    system : str
        This specifies the type of SOAP platform being defined. In this case
            it should probably always be KEPLER.
    object_name : str
        This is the identification label the platform will have. This is what 
            will be refered to when adding links in the anaysis reports.
    body : str
        This is the celestial body the platform is orbiting. Must match the 
            internal labeling SOAP uses. Inspect `.orb` file if necessary.
            For example, Earth, Moon, Mars, Sun.
    ic_type : str
        This specifies the coordinate system used. 
            Should always be set to `CLASSICAL`. 
    orbit_type : str
        This specifies the orbit type.
            Should always be set to `CUSTOM`.

    semi_major_axis : str
        Half the distance between the apoapsis and periapsis (in km).
    eccentricity : str
        Shape of the ellipse describing how much elongated compared to circle.
    inclination : str
        Vertical tilt of the ellipse with respect to the reference plane 
            (in degrees).
    ra_of_asc_node : str
        Longitude of the ascending node. Horizontally orients the ascending node
            of the ellipse (in degrees).
    arg_of_pericenter : str
        Argument of periapsis. The orientation of the ellipse in the orbital 
            plane (in degrees).
    mean_anomaly : str
        Defines the position of the orbiting body along the ellipse at a 
            specific time expressed as an angle (in degrees).

    year : str
        Year of the specified epoch
    month : str
        Month of the specified epoch
    day : str
        Day of the specified epoch
    hour : str
        Hour of the specified epoch
    minute : str
        Minute of the specified epoch
    second : str
        Second of the specified epoch

    Returns
    -------
    obj : dict:
        This is a dictionary matching the corresponding keys and values.

        This is used to fill in the template `platform_custom.orb` by using
            `content.format(**obj)`with `content` the text of the template.
    """

    platform = {}

    platform["system"] = system # ex : NORAD, KEPLER, ECR_FIXED, ECI_FIXED
    platform["object_name"] = object_name
    platform["body"] = body # ex : Earth, Moon, Mars, Sun
    platform["ic_type"] = ic_type
    platform["orbit_type"] = orbit_type # ex : CUSTOM, GEOSYNCHRONOUS
    platform["semi_major_axis"] = semi_major_axis
    platform["eccentricity"] = eccentricity
    platform["inclination"] = inclination
    platform["ra_of_asc_node"] = ra_of_asc_node
    platform["arg_of_pericenter"] = arg_of_pericenter
    platform["mean_anomaly"] = mean_anomaly
    platform["year"] = year
    platform["month"] = month
    platform["day"] = day
    platform["hour"] = hour
    platform["minute"] = minute
    platform["second"] = second
    
    return platform

def create_ground_platform(
    name: str,
    latitude: str,
    longitude: str,
    altitude: str,
    body: str = "Earth"
) -> dict:
    """
    This function creates a dictionary object used to fill in the 
        `platform_ground.orb` template.

    Parameters
    ----------
    name : str
        This is the identification label the platform will have. This is what 
            will be refered to when adding links in the anaysis reports.
    latitude : str
        The latitude coordinates of the platform (in degrees).
    longitude : str
        The longitude coordinates of the platform (in degrees).
    altitude : str
        The altitude of the platform (in km).
    body : str
        This is the celestial body the platform is orbiting. Must match the 
            internal labeling SOAP uses. Inspect `.orb` file if necessary.
            For example, Earth, Moon, Mars, Sun.

    Returns
    -------
    obj : dict:
        This is a dictionary matching the corresponding keys and values.

        This is used to fill in the template `platform_ground.orb` by using
            `content.format(**obj)`with `content` the text of the template.
    """
    
    platform = {}

    platform["object_name"] = name
    platform["latitude"] = latitude
    platform["longitude"] = longitude
    platform["altitude"] = altitude
    platform["body"] = body # can be Earth, Moon, Mars, etc.

    return platform

def add_platform(platform: dict) -> str:
    """
    This function loads the values specified by the dictionary `platform` into
        the appropriate template for the type of platform given.
    
    Parameters
    ----------
    platform : dict
        This is a dictionary which stores the values specifying a platform.
            This should be obtained from one of the following functions.
            `create_norad_platform`,
            `create_custom_platform`,
            `create_ground_platform`

    Returns
    -------
    str
        This is the text of the template with the variables filled in by the 
            values of `platform`.
    """

    match len(platform):
        case 16: # norad
            template = osu.read_file(base_path / "data/templates/platform_norad.orb")
        case 17: # custom
            template = osu.read_file(base_path / "data/templates/platform_custom.orb")
        case 5: # ground
            template = osu.read_file(base_path / "data/templates/platform_ground.orb")
        case _:
            template = None

    return template.format(**platform)

def get_tle_platforms(source: str, fmt: str = "csv") -> list[dict]:
    """
    This function returns all the satellites in the file `{source}.{fmt}`.

    Parameters
    ----------
    source : str
        This should be the name of a tle source file in {fmt} format.
            `base_path / data / {fmt} / {source}.{fmt}`

    Returns
    -------
        A list of dictionary objects consisting of the data of the specified 
            platforms.
    """
    filepath = base_path / f"data/{fmt}/{source}.{fmt}"

    if fmt == "csv":
        csv_data = pd.read_csv(filepath).astype(str)
        rows = csv_data.iterrows()
    elif fmt == "tle":
        content = osu.read_file(filepath)
        lines = [l for l in content.split("\n") if l]

        length = len(lines)
        assert length % 3 == 0

        rows = []
        for i in range(length // 3):
            j = 3 * i
            satellite = Satrec.twoline2rv(lines[j + 1], lines[j + 2])
            rows.append(exporter.export_omm(satellite, lines[j].strip()))
        rows = enumerate(rows)
    else:
        rows = None

    platforms = []
    for index, platform_df in rows:

        satellite = Satrec()
        omm.initialize(satellite, platform_df)

        platform = create_norad_platform(
            object_name = platform_df["OBJECT_NAME"],
            norad_cat_id =  platform_df["NORAD_CAT_ID"],
            epoch_year = satellite.epochyr,
            epoch_fraction = satellite.epochdays,
            mean_motion_dot = platform_df["MEAN_MOTION_DOT"],
            mean_motion_ddot = platform_df["MEAN_MOTION_DDOT"],
            bstar = platform_df["BSTAR"],
            ephemeris_type = platform_df["EPHEMERIS_TYPE"],
            element_set_no = platform_df["ELEMENT_SET_NO"],
            inclination = platform_df["INCLINATION"],
            ra_of_asc_node = platform_df["RA_OF_ASC_NODE"],
            eccentricity = platform_df["ECCENTRICITY"],
            arg_of_pericenter = platform_df["ARG_OF_PERICENTER"],
            mean_anomaly = platform_df["MEAN_ANOMALY"],
            mean_motion = platform_df["MEAN_MOTION"],
            rev_at_epoch = platform_df["REV_AT_EPOCH"]
        )
        platforms.append(platform)

    return platforms

def get_lunar_platforms() -> list[dict]:
    """
    This function provides eight hard-coded satellites orbiting the moon.

    Returns
    -------
    list[dict]
        A list of dictionary objects consisting of the data of 
            Lunar platforms.
    """
    filepath = base_path / "data/orb/lunar_scenario.orb"
    platforms = op.parse_platforms(filepath)

    platforms = [create_custom_platform(**p) for p in platforms]

    return platforms

def get_martian_platforms() -> list[dict]:
    """
    This function provides eight hard-coded satellites orbiting Mars.

    Returns
    -------
    list[dict]
        A list of dictionary objects consisting of the data of 
            Martian platforms.
    """

    filepath = base_path / "data/orb/martian_scenario.orb"
    platforms = op.parse_platforms(filepath)
    platforms = [p for p in platforms if (p["body"] == "Mars" and len(p) > 5)]

    platforms = [create_custom_platform(**p) for p in platforms]

    return platforms

def sample_platforms(platforms: list[dict], k: int) -> list[dict]:
    """
    This function returns a random sample of `k` elements from `platforms`.

    Parameters
    ----------
    platforms : list[dict]
        This is a list of SOAP platforms as dictionaries.
    k : int
        This is the number of elements that are to be sampled from `platforms`

    Returns
    -------
    list[dict]
        A list containing `k` random elements from `platforms`.
    """

    return random.sample(platforms, k)

if __name__ == "__main__":

    # read tdrss tle data
    platform_df = csv_data.loc[0].to_dict()

    # create platform
    satellite = Satrec()
    omm.initialize(satellite, platform_df)

    platform = create_norad_platform(
        object_name = platform_df["OBJECT_NAME"],
        norad_cat_id =  platform_df["NORAD_CAT_ID"],
        epoch_year = satellite.epochyr,
        epoch_fraction = satellite.epochdays,
        mean_motion_dot = platform_df["MEAN_MOTION_DOT"],
        mean_motion_ddot = platform_df["MEAN_MOTION_DDOT"],
        bstar = platform_df["BSTAR"],
        ephemeris_type = platform_df["EPHEMERIS_TYPE"],
        element_set_no = platform_df["ELEMENT_SET_NO"],
        inclination = platform_df["INCLINATION"],
        ra_of_asc_node = platform_df["RA_OF_ASC_NODE"],
        eccentricity = platform_df["ECCENTRICITY"],
        arg_of_pericenter = platform_df["ARG_OF_PERICENTER"],
        mean_anomaly = platform_df["MEAN_ANOMALY"],
        mean_motion = platform_df["MEAN_MOTION"],
        rev_at_epoch = platform_df["REV_AT_EPOCH"]
    )

    # test norad platform builder (from TLE data)
    platform_text = add_platform(platform)

    assert len(platform_text.split()) == 39 # `TDRS 3` contributes extra space
    assert  platform_df["OBJECT_NAME"] in platform_text

    # test custom platform builder : moon
    platforms = get_lunar_platforms()
    platform_text = add_platform(platforms[0])

    assert len(platform_text.split()) == 40
    assert "ARTEMIS1" in platform_text

    # test custom platform builder : mars
    platforms = get_martian_platforms()
    platform_text = add_platform(platforms[0])

    assert len(platform_text.split()) == 41
    assert "MarsSat 1" in platform_text

    # test ground platform builder : albany
    platform = create_ground_platform(
        name = "Ground:Albany", 
        latitude = 42.68501266345616, 
        longitude = -73.82479012295363, 
        altitude = 0.0
    )
    platform_text = add_platform(platform)

    assert len(platform_text.split()) == 22
    assert "Albany" in platform_text

def add_link(source: str, target: str, name: str | None = None) -> str:
    """
    This function returns the text of a link object for a SOAP orb file.

    Parameters
    ----------
    source : str
        This is the name of the source platform.
    target : str
        This is the name of the target platform.
    name : str | None
        This is the internal label for the link.

    Returns
    -------
    str
        The text of a link object for an orb file.
    """
    if name == None:
        name = f"Link {source} - {target}"

    template = osu.read_file(base_path / "data/templates/link.orb")
    text = template.format(
        link_name = name,
        source = source,
        target = target
    )

    return text

def add_transmitter(name: str) -> str:
    """
    This function returns a transmitter object for the specified platform.
    """
    template = osu.read_file(base_path / "data/templates/transmitter.orb")
    return template.format(object_name = name)

def add_receivers(source: str, target: str) -> str:
    """
    This function returns a receiver link object between two platforms.
    """
    template = osu.read_file(base_path / "data/templates/receiver.orb")
    return template.format(a = source, b = target)

def add_analysis_variable(variable: str, source: str, target: str) -> str:
    """
    This function returns an analysis variable object between two platforms.

    Parameters
    ----------
    variable : str
        This is a valid SOAP analysis variable, e.g., `RX_TPOWER`.
    source : str
        This is the internal label for the source.
    target : str
        This is the internal label for the target.

    Returns
    -------
    str
        The text of the analysis variable object for an orb file.
    """
    template = osu.read_file(base_path / "data/templates/analysis_variable.orb")

    text = template.format(
        a = source,
        b = target,
        variable = variable,
        lower = -998,
        upper = 30
    )

    return text

def add_contact_analysis(pairs: list[tuple[str]], step_size: int, name: str, duration: int) -> str:
    template = osu.read_file(base_path / "data/templates/analysis_report.orb")

    variables = [f'\t"{source} - {target}"\n' for (source, target) in pairs]
    # print(pairs)

    text = template.format(
        variables = "".join(variables),
        step_size = step_size,
        name = name,
        duration = duration
    )

    return text

def generate_orb(
    platforms: list[dict],
    name: str,
    d: date,
    step_size: int = 3_600,
    duration: int = 86_400
) -> str:
    """
    This function returns an orb file with the given platforms set to generate 
        the specified reports. 

    This can be modified to controll different variables by replacing them in 
        the `base.orb` template with a variable and making the appropriate 
        changes to the `add_base` function.

    Returns
    -------
    platforms : list[dict]
        A list of platforms which are dictionary objects representing norad,
            custom, or ground stations. In particular, they must be objects 
            that can be handled by the function `add_platform`.
    name : str
        Name to be used for saving the reports.
    d : date
        Date for the simulation to start its run.
    step_size : int
        For reports that are calculated based on a set step size (in seconds).
    duration : int
        The duration of the simulation for the reports to run, starting at 
            date `d` (in seconds)

    Returns
    -------
    str
        This is the text of a valid orb file that will generate the reports
            automatically when opened by SOAP.
    """

    # get base 
    text = add_base(d) + "\n\n"

    # add platforms
    for platform in platforms:
        text += add_platform(platform) + "\n"

    # add transmitters
    for platform in platforms:
        text += add_transmitter(platform["object_name"]) + "\n"

    pairs = combinations(platforms, 2)
    pairs = [(pair[0]["object_name"], pair[1]["object_name"]) for pair in pairs]

    # add links
    for source, target in pairs:
        text += add_link(source, target) + "\n"

    # add RX_TPOWER analysis variables
    for source, target in pairs:
        text += add_analysis_variable("RX_TPOWER", source, target) + "\n"

    # add receivers
    for source, target in pairs:
        text += add_receivers(source, target) + "\n"

    # add contact analysis report 
    #   (requires transmitters, receivers and receiver analysis variables)
    text += add_contact_analysis(pairs, step_size, name, duration)

    return text

text = generate_orb(sample_platforms(get_tle_platforms("starlink"), 20), "test", TODAY)
# text = generate_orb([], "test", TODAY)
with open(base_path / "outputs/test.orb", "w") as f:
    f.write(text)