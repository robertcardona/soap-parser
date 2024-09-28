# soap-utils

`soap-utils` is a python library for programmatically interact with the 
*Satellite Orbin Analysis Program* (SOAP).
It can be used to create `.orb` files which are the SOAP filetype, and specify
custom reports to be generated. The `.orb` files can then be run in batch form
to generate `.csv` reports as specified in the `.orb` files.

## Installation

## Usage

## Contributing

You may need to make addotopms pr modifications to 
`orb_builder` and `report_parser`. 
If SOAP updates to a version that can no longer read the `.orb` files generated
by `orb_builder` or they modify the structure of the generated reports, 
breaking `report_parser` then parts of this codebase would have to be updated.

To begin, open SOAP and save the initial (blank) scenario as `base.orb`. 
Modify the relevant entries to be variables as the template `base.orb` file has.
Continue modifying the other template files if they continue breaking the 
SOAP interpreter upon loading in the generated `orb` files.

If you need other planets, the initial SOAP scenario is not enough and you'll 
need to make sure the `base.orb` template has access to the necessary planets
to begin with.

To make an addition, save your project, make a single addition, either an
analysis variable, a new type of platform, or a report, and then save that file 
with a different name. Then do a diff on the two `.orb` files to see what was 
added. You might need to make a new template `.orb` file containing the entry 
added and replacing certain values as variables. An associated function needs
to be added into `orb_generator` which replaces the variables of the template
with specfied ones. Then the appropriate modification / addition needs to be 
added to the `generate_orb` function.

Note : it is possible that the location of where the new additions are added 
in the orb file is relative to other entries and need to be added more 
carefully. If this happens, `generate_orb` might need to be rewritten to handle 
this. One way to see this is to generate the file as is, open it in SOAP, make 
a small modification, then revert it, then save the file. SOAP will rearrange
the entire file into the way it natively arranges it.

## Contributors

Robert Cardona, Brian Heller

## License