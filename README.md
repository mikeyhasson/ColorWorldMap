# ColorWorldMap
SVG tool that colors chosen countries in the World Map, and crop-masks irrelevant areas.

**Command line arguments variations are as follows:**

  1. <code>python ColorWorldMap.py bilateral country1-country2</code> 
  State two country names seperated by "-", where country names are corespondent to the index (but generally similar). The first will be colored green and the second orange. output file is "country1-country2 locator.svg"  
  
  2. <code>python ColorWorldMap.py bilateral country1-country2 instructions_file</code>
      same as bilateral except specifing colors in instructions_file.

  3. <code>python ColorWorldMap.py all filename instructions_file</code> 
     specify as many countries as you'd like in the instructions_file, all will be colored according to the first, or randomized color if wasn't specified. 
  
  4. <code>python ColorWorldMap.py filename instructions_file</code>
       define coloring freely.
 
 **instructions_file:**
 
  each line contains: country,color
  color is either #hex or literal css color name.
  
 **other language**
 
   you can specify a chosen language code by appending "-#CODE" to the mode name. eg. bilateral-he for Hebrew.
   Will look for match in wikidata to translate the name.
 
