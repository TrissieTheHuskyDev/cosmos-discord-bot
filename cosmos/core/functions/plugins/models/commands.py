from discord.ext.commands import Command, Group


class CosmosCommand(Command):

    def __init__(self, function, inescapable=True, **kwargs):
        if inescapable:
            self.disabled_channels = []
        self.inescapable = inescapable
        super().__init__(function, **kwargs)


class CosmosGroupCommand(Group):

    def __init__(self, *args, inescapable=True, **kwargs):
        self.inescapable = inescapable
        super().__init__(*args, **kwargs)


def cosmos_command(name: str = None, cls=None, **attrs):

    cls = cls or CosmosCommand

    def decorator(function):
        if isinstance(function, CosmosCommand):
            raise TypeError('Callback is already a command.')
        return cls(function, name=name, **attrs)

    return decorator


def cosmos_group_command(name: str = None, **attrs):
    attrs.setdefault('cls', CosmosGroupCommand)
    return cosmos_command(name=name, **attrs)
