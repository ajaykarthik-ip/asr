from fabric import Connection


class WPCommandRunner:
    def __init__(self, host, user, port=22, wp_path="/home/ubuntu/wordpress"):
        self.wp_path = wp_path
        self.connection = Connection(host=host, user=user, port=port)

    def run_command(self, command):
        result = self.connection.run(command, hide=True)
        return result.stdout.strip()

    def run_wp_cli(self, command):
        # Connect to the server and change to the WordPress directory
        # Run the command from the WordPress installation directory or
        # wp cli will not work.
        wp_command = f"cd {self.wp_path} && {command}"
        result = self.connection.run(wp_command, hide=True)
        return result.stdout.strip()

    def close(self):
        self.connection.close()
