from capabilitiesgenerator import CapabilitiesGenerator

capabilities_generator = CapabilitiesGenerator()

capabilities_generator.add_constraint("""
Only use your available capabilites
""")
capabilities_generator.add_constraint("""
Respond with a clear, singular action to perform
""")
capabilities_generator.add_constraint("""
Write files in .md Markdown format only
""")
capabilities_generator.add_constraint("""
Remember your previous actions and don't repeat steps
""")
capabilities_generator.add_constraint("""
Build on your previous actions and stay focused on the current task before moving to the next
""")
capabilities_generator.add_constraint("""
Only browse links that have been directly given to you by a google search
""")
capabilities_generator.add_constraint("""
If a website did not provide the information you needed, do not revisit it
""")
capabilities_generator.add_constraint("""
Writing to files will overwrite their content. Append to files instead to add to their content
""")
capabilities_generator.add_constraint("""
The AI system can only run one command at a time, so only one action should be performed per task
""")
capabilities_generator.add_constraint("""
Do not create a file unless you have information to write to it
""") 
capabilities_generator.add_constraint("""
No knowledge of up-to-date information without doing research
""") 

capabilities_generator.add_capability("""
Filesystem operations to organize your thoughts and output
""")
capabilities_generator.add_capability("""
Internet access to access current information
""")
capabilities_generator.add_capability("""
Long Term Memory management using files
""")
capabilities_generator.add_capability("""
Ability to browse links provided by a google search
""")
capabilities_generator.add_capability("""
A list of commands to help complete tasks
""")