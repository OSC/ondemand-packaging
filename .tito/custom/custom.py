
from tito.builder.main import Builder
from tito.common import create_builder

class SRPMBuilder(Builder):
    def __init__(self, name=None, tag=None, build_dir=None,
                 config=None, user_config=None,
                 args=None, **kwargs):

        # Mock builders need to use the packages normally configured builder
        # to get at a proper SRPM:
        self.normal_builder = create_builder(name, tag, config,
                build_dir, user_config, args, **kwargs)

        Builder.__init__(self, name=name, tag=tag,
                build_dir=build_dir, config=config,
                user_config=user_config,
                args=args, **kwargs)

    def srpm(self, dist=None):
        """
        Build a source RPM.
        MockBuilder will use an instance of the normal builder for a package
        internally just so we can generate a SRPM correctly before we pass it
        into mock.
        """
        self.normal_builder.srpm(dist)
        self.srpm_location = self.normal_builder.srpm_location
        self.artifacts.append(self.srpm_location)

    def rpm(self):
        pass

    def cleanup(self):
        if self.normal_builder:
            self.normal_builder.cleanup()
