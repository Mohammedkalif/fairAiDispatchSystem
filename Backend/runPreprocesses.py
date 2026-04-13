from Backend.prePreocess.cluster import main as clusterMain
from Backend.prePreocess.getRoute import main as getRouteMain
from Backend.prePreocess.routeFeatures import main as routeFeatureMain
from Backend.prePreocess.packageFeatures import main as packageFeatureMain
from Backend.prePreocess.finalFeatures import main as finalFeatureMain

DATA_DIR_TEMPLATE = "data/jsonFiles{}/"

def main(data_id):
    data_path = DATA_DIR_TEMPLATE.format(data_id)

    clusterMain(data_path)
    getRouteMain(data_path)
    routeFeatureMain(data_path)
    packageFeatureMain(data_path)
    finalFeatureMain(data_path)


if __name__ == "__main__":
    import sys
    data_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    main(data_id)