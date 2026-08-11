
import asyncio

from asyncua import Client

ENDPOINT = "opc.tcp://localhost:4840"
NAMESPACE_URI = "IndustrialSimulator"
POLL_INTERVAL = 1.0
POLL_COUNT = 10


async def main():

    async with Client(url=ENDPOINT) as client:

        ns_idx = await client.get_namespace_index(NAMESPACE_URI)

        objects = client.nodes.objects

        plant = await objects.get_child(
            f"{ns_idx}:IndustrialSimulator"
        )

        active_screen_node = await plant.get_child(
            f"{ns_idx}:ActiveScreenID"
        )

        active_screen_name_node = await plant.get_child(
            f"{ns_idx}:ActiveScreenName"
        )

        historicos = await plant.get_child(
            f"{ns_idx}:Historicos"
        )

        history_children = await historicos.get_children()

        tag_nodes = {}

        for child in history_children:

            name = (await child.read_browse_name()).Name
            tag_nodes[name] = child

        # Ordena Tag1, Tag2, ... numericamente
        tag_names_sorted = sorted(
            tag_nodes.keys(),
            key=lambda name: int(name.replace("Tag", ""))
        )

        last_values = {}

        for i in range(POLL_COUNT):

            screen_id = await active_screen_node.read_value()
            screen_name = await active_screen_name_node.read_value()

            print(f"\n=== Leitura {i + 1} | Tela ativa: {screen_id} ({screen_name}) ===")

            for tag_name in tag_names_sorted:

                node = tag_nodes[tag_name]
                values = await node.read_value()

                last_three = values[-3:]

                changed = ""
                if tag_name in last_values:
                    if last_values[tag_name] != values:
                        changed = "  <-- MUDOU (histórico ativo)"
                    else:
                        changed = "  (sem mudança)"

                print(f"  {tag_name}: últimos 3 = {last_three}{changed}")

                last_values[tag_name] = values

            await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())