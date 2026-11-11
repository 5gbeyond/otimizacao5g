"""Recalcula os cenários de máxima cobertura da Figura 15."""
import argparse
import csv
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, PowerNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
from osgeo import gdal, ogr, osr
from PIL import Image


def calculate(archive, baseline):
    gdal.UseExceptions()
    source = gdal.OpenEx(f"/vsizip/{archive.resolve()}/GO_setores_CD2022.shp",
                         gdal.OF_VECTOR)
    layer = source.GetLayer()
    layer.SetAttributeFilter("CD_MUN = '5208707'")
    projected = osr.SpatialReference()
    projected.ImportFromEPSG(31982)
    geographic = osr.SpatialReference()
    geographic.ImportFromEPSG(4326)
    for crs in (geographic, projected):
        crs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    forward = osr.CoordinateTransformation(geographic, projected)
    inverse = osr.CoordinateTransformation(projected, geographic)
    sector_transform = osr.CoordinateTransformation(layer.GetSpatialRef(), projected)
    xmin, xmax, ymin, ymax = -49.4187, -49.1094, -16.802, -16.558
    x0, y0, _ = forward.TransformPoint(xmin, ymin)
    x1, y1, _ = forward.TransformPoint(xmax, ymax)
    xe = np.arange(np.ceil(x0 / 1000) * 1000, np.floor(x1 / 1000) * 1000 + 1, 1000)
    ye = np.arange(np.ceil(y0 / 1000) * 1000, np.floor(y1 / 1000) * 1000 + 1, 1000)
    nx, ny = len(xe) - 1, len(ye) - 1
    x, y = np.meshgrid(np.arange(xe[0] + 50, xe[-1], 100),
                       np.arange(ye[0] + 50, ye[-1], 100))
    vector = ogr.GetDriverByName("Memory").CreateDataSource("")
    sectors = vector.CreateLayer("sectors", projected)
    sectors.CreateField(ogr.FieldDefn("idx", ogr.OFTInteger))
    population, rural = [0.0], [False]
    for record in layer:
        polygon = record.GetGeometryRef().Clone()
        polygon.Transform(sector_transform)
        item = ogr.Feature(sectors.GetLayerDefn())
        item.SetField("idx", len(population))
        item.SetGeometry(polygon)
        sectors.CreateFeature(item)
        population.append(float(record["v0001"]) * 10000 / polygon.GetArea())
        rural.append(record["SITUACAO"] == "Rural")
    raster = gdal.GetDriverByName("MEM").Create("", nx * 10, ny * 10, 1, gdal.GDT_Int32)
    raster.SetGeoTransform((xe[0], 100, 0, ye[-1], 0, -100))
    raster.SetProjection(projected.ExportToWkt())
    gdal.RasterizeLayer(raster, [1], sectors, options=["ATTRIBUTE=idx"])
    indices = raster.ReadAsArray()[::-1]
    valid = indices > 0
    pop = np.asarray(population)[indices]
    rural = np.asarray(rural)[indices]
    lon, lat, *_ = np.asarray(inverse.TransformPoints(
        np.column_stack((x.ravel(), y.ravel())))).T
    image = np.asarray(Image.open(baseline).convert("RGB"))
    px = np.clip(np.rint(290 + (lon - xmin) / (xmax - xmin) * 1302), 290, 1591)
    py = np.clip(np.rint(57 + (ymax - lat) / (ymax - ymin) * 1072), 57, 1128)
    px = 290 + ((px - 290) // 39.48 * 39.48 + 19).astype(int)
    py = 57 + ((py - 57) // 39.75 * 39.75 + 19).astype(int)
    rgb = image[py, px]
    covered = ((rgb >= [170, 175, 180]) & (rgb <= [185, 193, 200])).all(axis=1)
    covered = covered.reshape(valid.shape) & valid
    available = valid & ~covered

    def aggregate(values):
        return values.reshape(ny, 10, nx, 10).sum(axis=(1, 3))

    cx, cy = np.meshgrid(xe[:-1] + 500, ye[:-1] + 500)
    eligible = (aggregate(valid) > 50) & (aggregate(covered) < 50)
    candidates = np.column_stack((cx[eligible], cy[eligible]))
    distance2 = ((candidates[:, 0, None] - x[available]) ** 2
                 + (candidates[:, 1, None] - y[available]) ** 2)
    weights = pop[available], rural[available]
    rows = []
    for radius in (500, 1000, 1500, 4000):
        reaches = distance2 <= radius ** 2
        best = [None, None]
        for sites in combinations(range(len(candidates)), 3):
            gain = reaches[sites[0]] | reaches[sites[1]] | reaches[sites[2]]
            scores = tuple(w[gain].sum().item() for w in weights)
            for objective in (0, 1):
                rank = scores[objective], scores[1 - objective]
                if best[objective] is None or rank > best[objective][0]:
                    best[objective] = rank, sites, gain, scores
        if radius == 1000:
            draw(aggregate(pop), aggregate(rural), aggregate(valid), aggregate(covered),
                 best, available, candidates, xe, ye)
        for objective, (_, sites, _, scores) in zip(("population", "rural_area"), best):
            coords = inverse.TransformPoints(candidates[list(sites)])
            rows.append((radius, objective, *scores,
                         " | ".join(f"{lon:.6f}, {lat:.6f}" for lon, lat, *_ in coords)))
    with open("sensibilidade_figura15.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(("radius_m", "objective", "additional_residents",
                         "additional_rural_sector_hectares", "sites_lon_lat"))
        writer.writerows(rows)
    print(f"{len(candidates)} candidate sites, {len(list(combinations(candidates, 3)))} trios")
    for row in rows:
        print(row)


def draw(pop, rural, valid, covered, best, available, candidates, xe, ye):
    ny, nx = pop.shape
    extent = (0, nx, 0, ny)
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharex=True, sharey=True)
    fig.subplots_adjust(left=.07, right=.99, top=.96, bottom=.20, wspace=.11)
    for index, (ax, values, cmap) in enumerate(zip(axes, (pop, rural), ("Blues", "Greens"))):
        ax.imshow(np.ma.masked_where(valid == 0, values), origin="lower", extent=extent,
                  cmap=cmap, norm=PowerNorm(.45, vmax=np.percentile(values[values > 0], 98)))
        ax.contour(np.arange(nx) + .5, np.arange(ny) + .5, covered, levels=[50],
                   colors="#36485c", linewidths=.9, linestyles="dashed")
        _, sites, gain, _ = best[index]
        gain_grid = np.zeros(available.shape, dtype=bool)
        gain_grid[available] = gain
        ax.imshow(np.ma.masked_where(~gain_grid, gain_grid), origin="lower", extent=extent,
                  cmap=ListedColormap(["#11aa99"]), alpha=.62, interpolation="nearest")
        xy = (candidates[list(sites)] - [xe[0], ye[0]]) / 1000
        ax.scatter(*xy.T, marker="*", s=125, c="#e89038", edgecolors="#793e10",
                   linewidths=.7, zorder=5)
        ax.text(.025, .96, f"({chr(97 + index)})", transform=ax.transAxes,
                va="top", fontweight="bold", fontsize=13)
        ax.set(xlabel="East–west distance (km)", xlim=(0, nx), ylim=(0, ny))
    axes[0].set_ylabel("North–south distance (km)")
    fig.legend(handles=[
        Patch(color="#74a9cf", label="(a) Estimated population"),
        Patch(color="#74c476", label="(b) Rural census sectors"),
        Line2D([], [], ls="--", color="#36485c", label="Approximate baseline coverage boundary"),
        Patch(color="#11aa99", alpha=.62, label="Estimated coverage gain (1 km radius)"),
        Line2D([], [], marker="*", color="#e89038", ls="", markersize=12,
               label="Hypothetical new base station"),
    ], loc="lower center", bbox_to_anchor=(.5, .035), ncol=3, frameon=False)
    fig.savefig("Figura15_Goiania_1km.png", dpi=300, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ibge_zip", type=Path)
    parser.add_argument("baseline_png", type=Path)
    args = parser.parse_args()
    calculate(args.ibge_zip, args.baseline_png)
