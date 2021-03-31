Kaleido Interview
=================
**Problem Statement:**  
Chemists need to register or store compounds so that they can be tracked 
when they are used in experiments. Once a compound is registered, plates 
can be prepared and the compounds can go in a well in a plate. For Data 
Scientists to run analysis, they need to know which compound
is contained in which well.  
  
**Minimum Requirements:**  
* Allow the user to store/register a Compound ID (str)
* Allow association of a Compound to a well (str/str)
* Allow the user to transfer contents from a well to 1...n wells
* Given a well ID return what the Compound ID is in it  

**Environment:** OSX

## Building the Code
The program can be installed using the following steps:

    $ git clone https://github.com/esameth/kaleido.git
    $ cd [path/to/setup.py]
    $ pip install -e .
     
You have successfully built the code!

## Running the Code
`kaleido` uses three commands: `compound`, `plate`, and `well`.  

### `compound` Command  
The `compound` command allows you to store, register, search, and delete
a compound. This can be done by using `kaleido compound [Compound ID]` with
one of the following tags: `--store`, `--register`, `--search`, or `--delete`.  
  
All compounds are stored in a json file (default=`compounds.json`). 
Chemists can store a compound using `--store` and register one using 
`--register`.  
**NOTE: (Assumption) Once a compound is registered, it cannot be changed to stored**  
  
Chemists or Data Scientists can then retrieve all of the properties of
a specific compound using `--search`, which will give the id, state (stored
or registered), and all wells that it is in.  
Example:  
    
    $ kaleido compound S --search
    Compound id: S
    State: registered
    
    Associated plates and wells: 
    P-12345.A1
    P-3.B4
    P-3.C2
    P-7.A4
    
If needed, a compound may also be deleted using `--delete`, which
will delete the compound from the compound.json file and remove the
compound from any wells.

### `plate` Command
The `plate` command allows you to create, search, or delete a plate, or 
add different compounds to wells in the plate. This is done using 
`kaleido plate [Plate ID]` with any of the following tags: `--create`,
`--search`, `--delete`, or `--add`. All plates are stored in a json 
file (default=`plates.json`), which contains the Plate ID, height, width,
and any wells that are taken along with their corresponding compound.
  
A Chemist may create a plate with a given set of dimensions. This will
represent the plate width and height, which makes up our plate.

    $ kaleido plate P-12345 --create 3 4
    Plate ID:	P-12345
    Num. rows:	3
    Num. cols:	4
    
        1   2   3   4
    A   -	-   -	-
    B   -	-   -	-
    C   -	-   -	-
    
We can then search for a plate and retrieve the output above using `--search`
to obtain a visualization of the plate.  
  
If a Chemist needs to add multiple compounds into one plate, they may
do so using `--add`. This takes as many inputs as needed in the format 
`[Well Position]=[Compound ID]`. For example:

    $ kaleido plate P-12345 --add A1=S --add B4=C
    Successfully added S to P-12345.A1
    Successfully added C to P-12345.B4
    
    Plate ID:	P-12345
    Num. rows:	3
    Num. cols:	4
    
        1   2   3	4
    A   S	-   -	-
    B   -	-   -	C
    C   -	-   -	-

**NOTE: Only registered compounds may be added to a plate**  

### `well` Command
The `well` command allows you to search or delete the given well,
add a compound to that well, or transfer the contents of that well to 
other wells. This is done using `kaleido well [Well ID]` with any of the 
following tags: `--search`, `--delete`, `--add`, or `--transfer`.  


In order for a Data Scientist to know the contents of a well, they may use:

    $ kaleido well P-12345.A1 --search
    Compound S is in P-12345.A1
    
If a Chemist wants to assign a compound to a specific well, they may do so
using `kaleido well [Plate ID] --add [Compound ID]`. Similarly, the contents of
a well may transferred to other wells. An example of this is as follows:

    $ kaleido well P-12345.A1 --transfer P-3.B4 P-3.C2 P-7.A4

**NOTE: Only registered compounds may be added or transferred to a well**

## Testing the Code
**Example:**
* A User Registers Compound **S**
* A User assigns Compound **S** to **P-12345.A1**
* A User takes the contents of **P-12345.A1** and put it in **P-3.B4**, **P-3.C2** and **P-7.A4**
* A User requests the Compound ID of the contents of **P-7.A4** and gets back **S**

An run-through based off of the example would be as follows and could be used for testing:

    $ kaleido compound S --register
    $ kaleido plate P-12345 --create 3 4
    $ kaleido plate P-3 --create 4 5
    $ kaleido plate P-7 --create 3 5
    $ kaleido well P-12345.A1 --add S
    $ kaleido well P-12345.A1 --transfer P-3.B4 P-3.C2 P-7.A4
    $ kaleido well P-7.A4 --search
