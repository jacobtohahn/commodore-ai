from capabilitiesgenerator import CapabilitiesGenerator

capabilities_generator = CapabilitiesGenerator()

capabilities_generator.add_constraint("""
Only use your available capabilites
""")

capabilities_generator.add_capability("""
Filesystem operations, including reading, writing, appending, and deleting files,
creating, moving, and deleting directories
""")
capabilities_generator.add_capability("""
Internet access by googleing a search term or browsing a website URL
""")