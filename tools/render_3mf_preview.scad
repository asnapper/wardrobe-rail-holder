// Helper for rendering a project thumbnail from an exported 3MF.
// Pass the source path on the command line, for example:
//   openscad -D 'model_file="project.3mf"' -o preview.png this-file.scad

model_file = "";

assert(model_file != "", "set model_file to the 3MF path");
import(model_file);
