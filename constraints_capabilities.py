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

capabilities_generator.add_capability("""
Filesystem operations, including reading, writing, appending, and deleting files,
creating, moving, and deleting directories
""")
capabilities_generator.add_capability("""
Internet access by googling a search term or browsing a website URL
""")