import jinja2
import json


def load_template(template_path, template_file, output_path,output_file_name,data):
    
    templateLoader = jinja2.FileSystemLoader(template_path)
    
    templateEnv = jinja2.Environment(loader=templateLoader)
    
    template = templateEnv.get_template(template_file) 
    
    input = data
    
    output_file = template.render(input)
        
    with open('{}/{}'.format(output_path,output_file_name), "w") as fh:
              
            fh.write(output_file)                         
    return
