from capabilitiesgenerator import CapabilitiesGenerator

capabilities_generator = CapabilitiesGenerator()

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
Browse links that have been given to you by a google search
""")
capabilities_generator.add_constraint("""
Once you have completed a task, do not repeat it again
""")
capabilities_generator.add_constraint("""
You cannot read files that do not exist
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
capabilities_generator.add_constraint("""
If you get stuck, recall your task, objective, and available commands. Backtrack and try a different strategy
""")
capabilities_generator.add_constraint("""
"Read article" refers to browsing a website, not a file
""")
capabilities_generator.add_constraint("""
Do not forget your overall objective
""")
capabilities_generator.add_constraint("""
Cite real, reputable sources in your notes
""")
capabilities_generator.add_constraint("""
No ability to click links on websites, so always use a full, direct link to the subpage
""")

capabilities_generator.add_capability("""
Filesystem operations to organize your thoughts and output, which should be utilized often
""")
capabilities_generator.add_capability("""
The list files command to understand your current filesystem
""")
capabilities_generator.add_capability("""
Internet access to access current information
""")
# capabilities_generator.add_capability("""
# Long Term Memory management using files
# """)
capabilities_generator.add_capability("""
Ability to browse links provided by a google search
""")
capabilities_generator.add_capability("""
A list of commands to help complete tasks
""")
capabilities_generator.add_capability("""
Creativity and problem solving skills
""")
capabilities_generator.add_capability("""
A comprehensive understanding of numerous topics and skills
""")