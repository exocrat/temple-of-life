"""ECS (entity-component-system) pattern."""


class Entity(abc.MutableMapping):
    """ECS entity."""

    def __init__(self, eid: int, world: World):
        if eid not in world.entities:
            raise NameError(f"entity ID {eid} does not exist")
        self.eid = eid
        self.world = world

    def __getattr__(self, attr: str) -> set:
        if attr == "components":
            return self.world.eid_comps[self.eid]
        if attr == "tags":
            return self.world.eid_tags[self.eid]
        if attr == "relations":
            return self.world.eid_rels[self.eid]
        else:
            raise AttributeError(f"'Entity' object has no attribute '{attr}'")

    def __getitem__(self, component: tuple[str, T]) -> T:
        return self.world.components[component][self.eid]

    def __setitem__(self, component: tuple[str, T], value: T) -> None:
        self.world.eid_comps[self.eid].add(component)
        self.world.components[component][self.eid] = value

    def __delitem__(self, component: tuple[str, T]) -> None:
        del self.world.components[component][self.eid]
        self.world.eid_comps[self.eid].remove(component)

    def __len__(self) -> int:
        return len(self.world.eid_comps[self.eid])

    def __iter__(self) -> iter:
        comps = self.world.eid_comps[self.eid]
        for comp in comps:
            yield comp

    def tag(self, tag: str | tuple[str, int]) -> None:
        """Add a tag."""
        if tag not in self.tags:
            self.world.eid_tags[self.eid].add(tag)
            self.world.tags[tag].add(self.eid)

    def untag(self, tag: str | tuple[str, int]) -> None:
        """Remove a tag."""
        if tag in self.tags:
            self.world.eid_tags[self.eid].remove(tag)
            tag_eids = self.world.tags[tag]
            tag_eids.remove(self.eid)
            if not tag_eids:
                del self.world.tags[tag]

    def relate(self, relation: str, other_id: int) -> None:
        """Add a relation with another entity."""
        if other_id not in world.entities:
            raise NameError(f"target EID {other_id} does not exist")
        relations = self.world.relations[relation]
        if relation in self.relations:
            relations[self.relations[relation]].remove(self.eid)
        self.relations[relation] = other_id
        if other_id not in relations:
            relations[other_id] = set()
        relations[other_id].add(self.eid)

    def unrelate(self, relation: str, other_id: int) -> None:
        """Remove a relation with another entity."""
        if other_id not in world.entities:
            raise NameError(f"target EID {other_id} does not exist")
        related = self.world.relations[relation][other_id]
        del self.relations[relation]
        related.remove(self.eid)
        if related == set():
            del self.world.relations[relation][other_id]


class World:
    """ECS registry."""

    def __init__(self):
        self.entities = set()
        self.components = defaultdict(dict)
        self.tags = defaultdict(set)
        self.relations = defaultdict(dict)
        self.eid_comps = dict()
        self.eid_tags = dict()
        self.eid_rels = dict()
        self.next_id = 0

    def create_entity(self) -> None:
        """Create an ECS entity in this registry."""
        eid = self.next_id
        self.next_id += 1
        self.entities.add(eid)
        self.eid_comps[eid] = set()
        self.eid_tags[eid] = set()
        self.eid_rels[eid] = dict()
        return Entity(eid, self)

    def delete_entity(self, eid: int) -> None:
        """Delete an ECS entity from this registry."""
        entity = Entity(eid, self)
        for comp in list(entity.components):
            del entity[comp]
        for tag in list(entity.tags):
            entity.untag(tag)
        for rel in list(entity.relations):
            entity.unrelate(rel, entity.relations[rel])
        del self.eid_comps[eid]
        del self.eid_tags[eid]
        del self.eid_rels[eid]
        for relation in self.relations:
            for cid in list(self.relations[relation].get(eid, set())):
                child = Entity(cid, world)
                child.unrelate(relation, eid)
        self.entities.remove(eid)

    def query(
        self,
        comps: list[tuple[str, type]] = [],
        tags: list[str | tuple[Position, Point]] = [],
        rels: list[tuple[str, int]] = []
    ) -> set[int]:
        """Furnish all entities with given attributes."""
        comp_sets = [set(self.components[comp]) for comp in comps]
        tag_sets = [self.tags[tag] for tag in tags]
        rel_sets = [self.relations[rel[0]].get(rel[1], set()) for rel in rels]
        comp_sets.sort(key = lambda seq: len(seq))
        tag_sets.sort(key = lambda seq: len(seq))
        rel_sets.sort(key = lambda seq: len(seq))
        comp_set = set.intersection(*comp_sets) if comp_sets else set()
        tag_set = set.intersection(*tag_sets) if tag_sets else set()
        rel_set = set.intersection(*rel_sets) if rel_sets else set()
        queried_sets = []
        if comps:
            queried_sets.append(comp_set)
        if tags:
            queried_sets.append(tag_set)
        if rels:
            queried_sets.append(rel_set)
        eid_set = set.intersection(*queried_sets)
        return eid_set
