# Instruction Set
|Instructions |Paramaters |Meaning                                            |
|-------------|-----------|---------------------------------------------------|
|set          |a b        |gets data from b and stores it in a                |
|sub          |a b c      |sets c to be equal to a - b                        |
|cmp          | a b c f   |compares a and c with condition b, if true run function f. A list of valid comparators is below|
|add          |a b c      |sets c to a + b                                    |
|runFunction  |f          |runs the function f                                |
|jump         |n          |add n to the current program counter               |
|newMemSeg    | n s       |create a new memory segment with name n and size s |
|setMemSeg    | n         | sets n to be the default memory address           |
|loadMem      | a A B C ..| stores an array of data A B C ... into memory starting at address a |
|skip         | a         | skips next line if a != 0                         |

# Cmp Reference Table
| b  | action          |
|----|-----------------|
| >  | if a > c run f  |
| =  | if a = c run f  |
| <= | if a <= c run f |

# Types
|type      | notation | meaning         | example |
|----------|----------|-----------------|---------|
|Immediate | \d+      | A simple number | 6       |
|Address   | \d+:n?| a number that represents a address in a certain memory segment reference by a string name n | 72:main|
|Reference | *\d+:n?      | reference a address in memory which holds the address of the target cell| *72:main      | 
|Register  | [rR]\d       | a simple register for temporary holding | R1 |

# Memory segments
Memory segments are different sections of memory each with their own address space, using an address as such `72:` with no segment specified implies that the machine should go to the current default memory secion. 
on startup this is called "main" but can be set to any memory segment via the `setMemSeg` command

# Registers
These act as tempory places to hold data but effectivly are just like memory. 
you can use r0 to r7.
by default all values in registers are immediate values but if you would like a register to be interperted as a address simply do `R0:`
you can further do `*R0:` to use the value in the address pointed to by the register as a reference

this does not support multiple memorgy segments though, only current. 

# Functions
to set up a small bit of code to run on a function call do
```
define [name]
   code ...
end
```
for example to define a function to add r0 and r1 and store the result into r0 we can do
```
define quickAdd
    add r0 r1 r0
end
```
and then call it as such
```
runFunction quickAdd
```

Functions are designed to be for small bits of code and to allow for conditional braching so do note

    DO NOT DEFINE SUBS INSIDE OF SUBS FOR THE LOVE OF GOD

    ALSO YOU CAN NOT JUMP INSIDE OF A SUB

    You should be able to call a function from another function although this is not well tested

In future there may be a full stack set up that allows for recurrsion and functions to have no limitations on them but at the moment the code is run seperately in it's own code space meaning jumping is impossible. 
Furthermore the current function being run is stored in a single variable rather then on a stack so recurrsion is impossible as well. 

# Cycles
The machine keeps track of its' own cycles, at the creation of the machiens you specify what is the max cycle count on the machine. 

This is to prevent infinite loops, once the cycle count is hit the program will stop. setting this to 1000 usually allows for a ample amount of code to be run and a infinite loop to be caught. 

# Example code
Code to add 5 and 6 together and store it at memory address 0 in the main memory segment
```
set r0 5
set r1 5
add r0 r1 0:
```
Code to create a new memory segment called results which is 256 cells long
```
newMemSeg results 256
```
Code to add 5 and 6 together and store it at memory address 0 in the results memory segment
```
newMemSeg results 256
set r0 5
set r1 5
add r0 r1 0:results
```
the same code as above but we set results to be our default memory section
```
newMemSeg results 256
setMemSeg results
set r0 5
set r1 5
add r0 r1 0:
```

A roundabout way of getting the data in cell 5 of memory segment main, into register 0
```
set 0: 5
set r0 *0:
```